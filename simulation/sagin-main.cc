#include "ns3/core-module.h"
#include "ns3/mobility-module.h"
#include "ns3/flow-monitor-module.h"

#include "topology.h"
#include "mobility.h"
#include "communication.h"
#include "task-model.h"
#include "task-queue.h"
#include "metrics.h"
#include "energy-model.h"
#include "offloading-engine.h"
#include "control-interface.h"
#include "state-export.h"

#include <unistd.h>

using namespace ns3;

NS_LOG_COMPONENT_DEFINE("SaginMain");

ControlInterface controller;
OffloadingEngine engine;
EnergyModel      energyModel;

/* ─── Task completion callback ──────────────────────────────── */
void TaskCompletionCallback(Metrics *metrics, OffloadingEngine *eng,
                            Task task, int routeId)
{
    double latency   = metrics->ComputeLatency(task);
    bool   deadlineMet = (latency <= task.deadline);

    metrics->LogTaskCompletion(
        Simulator::Now().GetSeconds(), latency, routeId, deadlineMet);
    metrics->RecordTaskCompletion(task.dataSize);

    eng->TaskCompleted(routeId);
}

/* ─── Main processing loop ──────────────────────────────────── *
 * Processes up to maxPerLoop tasks per second.
 * With 10 CHs generating every 1 second (taskInterval=1) we get
 * 10 tasks/s — deliberately exceeding UAV capacity (4) to force
 * intelligent multi-route distribution.
 */
void RunLoop(TaskQueue &queue, Metrics &metrics)
{
    int maxPerLoop = 15;   // drain up to 15 tasks per loop tick
    int processed  = 0;

    while(!queue.Empty() && processed < maxPerLoop)
    {
        Task task  = queue.Pop();
        int routeId = controller.GetRouteId();

        double estLatency = engine.Process(task, routeId);

        if(routeId == 0)
            energyModel.ConsumeCompute(task.cpuCycles);
        else
            energyModel.ConsumeTransmit(task.dataSize);

        Simulator::Schedule(
            Seconds(estLatency),
            &TaskCompletionCallback,
            &metrics, &engine, task, routeId);

        processed++;
    }

    Simulator::Schedule(Seconds(1.0), &RunLoop,
                        std::ref(queue), std::ref(metrics));
}

/* ─── Entry point ───────────────────────────────────────────── */
int main(int argc, char *argv[])
{
    uint32_t numCH    = 10;
    double   simTime  = 100.0;
    double   taskInterval = 1.0;   // generate tasks every 1 second
                                    // (was 2 s — doubling pressure)

    CommandLine cmd;
    cmd.AddValue("numCH",         "Number of cluster heads", numCH);
    cmd.AddValue("simTime",       "Simulation time (s)",     simTime);
    cmd.AddValue("taskInterval",  "Task generation interval",taskInterval);
    cmd.Parse(argc, argv);

    std::cout << "=== SAGIN Simulation ===" << std::endl;
    std::cout << "  Cluster heads : " << numCH       << std::endl;
    std::cout << "  Sim time      : " << simTime      << " s" << std::endl;
    std::cout << "  Task interval : " << taskInterval << " s" << std::endl;

    SaginTopology topo;
    topo.CreateNodes(numCH);
    InstallMobility(topo);
    InstallCommunication(topo);

    FlowMonitorHelper flowHelper;
    Ptr<FlowMonitor>  flowMonitor = flowHelper.InstallAll();

    TaskQueue queue;

    TaskModel taskModel;
    taskModel.SetQueue(&queue);
    taskModel.SetTaskInterval(taskInterval);
    taskModel.Start(topo);

    Metrics metrics;

    Ptr<ConstantVelocityMobilityModel> uav =
        topo.uavNode.Get(0)
            ->GetObject<ConstantVelocityMobilityModel>();

    controller.AttachUav(uav);
    controller.Start();

    std::cout << "Waiting for controller connection..." << std::endl;
    while(!controller.IsConnected())
        sleep(1);

    std::cout << "Controller connected — starting simulation." << std::endl;

    StateExport state;
    state.SetQueue(&queue);
    state.SetController(&controller);
    state.SetMetrics(&metrics);
    state.SetEnergyModel(&energyModel);
    state.SetOffloadingEngine(&engine);

    Simulator::Schedule(Seconds(1.0), &StateExport::SendState,
                        &state, std::ref(topo));
    RunLoop(queue, metrics);

    Simulator::Stop(Seconds(simTime));
    Simulator::Run();

    /* ── FlowMonitor output ──────────────────────────────── */
    flowMonitor->SerializeToXmlFile("sagin_flowmon.xml", true, true);

    std::cout << "\n=== FLOW MONITOR SUMMARY ===" << std::endl;
    flowMonitor->CheckForLostPackets();
    Ptr<Ipv4FlowClassifier> classifier =
        DynamicCast<Ipv4FlowClassifier>(flowHelper.GetClassifier());
    FlowMonitor::FlowStatsContainer stats = flowMonitor->GetFlowStats();

    for(auto &flow : stats)
    {
        Ipv4FlowClassifier::FiveTuple t =
            classifier->FindFlow(flow.first);
        if(flow.second.rxPackets > 0)
        {
            double avgDelay =
                flow.second.delaySum.GetSeconds() / flow.second.rxPackets;
            double throughput =
                flow.second.rxBytes * 8.0 /
                (flow.second.timeLastRxPacket.GetSeconds()
               - flow.second.timeFirstTxPacket.GetSeconds()) / 1e6;

            std::cout << "Flow " << flow.first
                      << " (" << t.sourceAddress
                      << "→" << t.destinationAddress << ")"
                      << "  delay=" << avgDelay << "s"
                      << "  tput="  << throughput << " Mbps"
                      << "  pkts="  << flow.second.rxPackets
                      << std::endl;
        }
    }
    std::cout << "=============================" << std::endl;

    metrics.PrintSummary();
    Simulator::Destroy();
    return 0;
}
