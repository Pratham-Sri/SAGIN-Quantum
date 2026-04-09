#include "state-export.h"

#include "ns3/core-module.h"
#include "ns3/mobility-module.h"

#include <iostream>
#include <sstream>
#include <cmath>

using namespace ns3;

StateExport::StateExport()
{
    m_queue = nullptr;
    m_controller = nullptr;
    m_metrics = nullptr;
    m_energy = nullptr;
    m_engine = nullptr;
}

void StateExport::SetQueue(TaskQueue *queue)
{
    m_queue = queue;
}

void StateExport::SetController(ControlInterface *controller)
{
    m_controller = controller;
}

void StateExport::SetMetrics(Metrics *metrics)
{
    m_metrics = metrics;
}

void StateExport::SetEnergyModel(EnergyModel *energy)
{
    m_energy = energy;
}

void StateExport::SetOffloadingEngine(OffloadingEngine *engine)
{
    m_engine = engine;
}

void StateExport::SendState(SaginTopology &topo)
{
    Ptr<MobilityModel> mob =
        topo.uavNode.Get(0)->GetObject<MobilityModel>();

    Vector pos = mob->GetPosition();
    Vector vel = mob->GetVelocity();
    double speed = sqrt(vel.x * vel.x + vel.y * vel.y);

    /* Consume flight energy based on actual speed */
    if(m_energy != nullptr)
    {
        m_energy->ConsumeFlight(speed);
    }

    double time = Simulator::Now().GetSeconds();

    int qsize = 0;
    if(m_queue != nullptr)
        qsize = m_queue->Size();

    int routeId = 0;
    if(m_controller != nullptr)
        routeId = m_controller->GetRouteId();

    double energy = 0.0;
    if(m_energy != nullptr)
        energy = m_energy->GetEnergy();

    /* Get per-node loads */
    double loads[6] = {0, 0, 0, 0, 0, 0};
    if(m_engine != nullptr)
    {
        for(int i = 0; i < 6; i++)
            loads[i] = m_engine->GetNodeLoad(i);
    }

    /* Get throughput from metrics */
    double throughputTasks = 0.0;
    double throughputBits = 0.0;
    double avgLatency = 0.0;
    if(m_metrics != nullptr)
    {
        throughputTasks = m_metrics->GetThroughputTasks();
        throughputBits = m_metrics->GetThroughputBits();
        avgLatency = m_metrics->GetAverageLatency();
    }

    /* Build expanded state message for controller:
       STATE time x y queue route energy
             load0 load1 load2 load3 load4 load5
             throughput avgLatency speed */

    std::ostringstream out;

    out << "STATE "
        << time << " "
        << pos.x << " "
        << pos.y << " "
        << qsize << " "
        << routeId << " "
        << energy << " "
        << loads[0] << " "
        << loads[1] << " "
        << loads[2] << " "
        << loads[3] << " "
        << loads[4] << " "
        << loads[5] << " "
        << throughputTasks << " "
        << avgLatency << " "
        << speed
        << "\n";

    /* Send state to controller */
    if(m_controller != nullptr)
    {
        m_controller->SendState(out.str());
        m_controller->WaitForCommand();
    }

    /* Log state to metrics */
    if(m_metrics != nullptr)
    {
        m_metrics->LogState(
            time, pos.x, pos.y,
            qsize, routeId, energy,
            throughputTasks, throughputBits,
            loads[0], loads[1], loads[2],
            loads[3], loads[4], loads[5],
            true);
    }

    /* Schedule next export */
    Simulator::Schedule(
        Seconds(1.0),
        &StateExport::SendState,
        this,
        std::ref(topo));
}
