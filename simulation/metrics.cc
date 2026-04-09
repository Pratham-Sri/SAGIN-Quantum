#include "metrics.h"

#include "ns3/core-module.h"

#include <iostream>

using namespace ns3;

Metrics::Metrics()
{
    logfile.open("sagin_metrics.csv");

    // CSV header: one row per COMPLETED TASK (latency will always be populated)
    logfile << "time,latency,queue,x,y,route,energy,"
            << "throughput_tasks,throughput_bits,"
            << "load0,load1,load2,load3,load4,load5,"
            << "deadline_met"
            << std::endl;

    totalLatency = 0.0;
    tasksCompleted = 0;

    m_windowStart = 0.0;
    m_tasksInWindow = 0;
    m_bitsInWindow = 0.0;
    m_throughputTasks = 0.0;
    m_throughputBits = 0.0;

    m_deadlinesMet = 0;
    m_deadlinesMissed = 0;

    m_lastX = 0.0;
    m_lastY = 0.0;
    m_lastQueueSize = 0;
    m_lastEnergy = 50000.0;
    for(int i = 0; i < 6; i++)
    {
        m_routeCount[i] = 0;
        m_routeLatency[i] = 0.0;
        m_lastLoad[i] = 0.0;
    }
}

Metrics::~Metrics()
{
    if(logfile.is_open())
        logfile.close();
}

double Metrics::ComputeLatency(Task task)
{
    double latency =
        Simulator::Now().GetSeconds() - task.creationTime;

    totalLatency += latency;
    tasksCompleted++;

    bool deadlineMet = (latency <= task.deadline);
    if(deadlineMet)
        m_deadlinesMet++;
    else
        m_deadlinesMissed++;

    return latency;
}

void Metrics::LogTaskCompletion(double time, double latency,
                                int routeId, bool deadlineMet)
{
    if(routeId >= 0 && routeId < 6)
    {
        m_routeCount[routeId]++;
        m_routeLatency[routeId] += latency;
    }

    /* Write one CSV row per completed task so the latency column
     * is ALWAYS populated.  State-level columns (x, y, queue, etc.)
     * are filled with the last-known values for context. */
    logfile << time
            << "," << latency
            << "," << m_lastQueueSize
            << "," << m_lastX
            << "," << m_lastY
            << "," << routeId
            << "," << m_lastEnergy
            << "," << m_throughputTasks
            << "," << m_throughputBits
            << "," << m_lastLoad[0]
            << "," << m_lastLoad[1]
            << "," << m_lastLoad[2]
            << "," << m_lastLoad[3]
            << "," << m_lastLoad[4]
            << "," << m_lastLoad[5]
            << "," << (deadlineMet ? 1 : 0)
            << std::endl;
}

void Metrics::LogState(
    double time,
    double x, double y,
    int queue,
    int route,
    double energy,
    double throughputTasks,
    double throughputBits,
    double load0, double load1,
    double load2, double load3,
    double load4, double load5,
    bool deadlineMet)
{
    /* Cache current state so LogTaskCompletion can use these values */
    m_lastX = x;
    m_lastY = y;
    m_lastQueueSize = queue;
    m_lastEnergy = energy;
    m_lastLoad[0] = load0;
    m_lastLoad[1] = load1;
    m_lastLoad[2] = load2;
    m_lastLoad[3] = load3;
    m_lastLoad[4] = load4;
    m_lastLoad[5] = load5;

    /* State-tick rows are no longer written here.
     * Only LogTaskCompletion writes CSV rows (one per completed task)
     * so that latency is always present. */
    (void)time; (void)route; (void)deadlineMet;
    (void)throughputTasks; (void)throughputBits;
}

void Metrics::LogQueueSize(int size)
{
    // kept for backward compatibility
}

void Metrics::RecordTaskCompletion(double dataSize)
{
    double now = Simulator::Now().GetSeconds();

    m_tasksInWindow++;
    m_bitsInWindow += dataSize;

    /* Sliding window: reset every 5 seconds */
    double windowDuration = now - m_windowStart;
    if(windowDuration >= 5.0)
    {
        m_throughputTasks = m_tasksInWindow / windowDuration;
        m_throughputBits = m_bitsInWindow / windowDuration;
        m_tasksInWindow = 0;
        m_bitsInWindow = 0.0;
        m_windowStart = now;
    }
}

double Metrics::GetThroughputTasks() const
{
    return m_throughputTasks;
}

double Metrics::GetThroughputBits() const
{
    return m_throughputBits;
}

double Metrics::GetAverageLatency() const
{
    if(tasksCompleted > 0)
        return totalLatency / tasksCompleted;
    return 0;
}

int Metrics::GetDeadlinesMet() const
{
    return m_deadlinesMet;
}

int Metrics::GetDeadlinesMissed() const
{
    return m_deadlinesMissed;
}

void Metrics::PrintSummary()
{
    double avgLatency = 0;
    if(tasksCompleted > 0)
        avgLatency = totalLatency / tasksCompleted;

    std::cout << "\n========== SIMULATION SUMMARY ==========" << std::endl;
    std::cout << "Tasks completed: " << tasksCompleted << std::endl;
    std::cout << "Average latency: " << avgLatency << " s" << std::endl;
    std::cout << "Throughput: " << m_throughputTasks << " tasks/s | "
              << m_throughputBits / 1e6 << " Mbps" << std::endl;
    std::cout << "Deadlines met: " << m_deadlinesMet
              << " | missed: " << m_deadlinesMissed << std::endl;

    if(m_deadlinesMet + m_deadlinesMissed > 0)
    {
        double metRatio = (double)m_deadlinesMet /
            (m_deadlinesMet + m_deadlinesMissed) * 100.0;
        std::cout << "Deadline success rate: " << metRatio << "%" << std::endl;
    }

    std::cout << "\nPer-route statistics:" << std::endl;
    for(int i = 0; i < 6; i++)
    {
        if(m_routeCount[i] > 0)
        {
            double avgRouteLatency =
                m_routeLatency[i] / m_routeCount[i];

            std::cout << "  Route " << i << ": "
                      << m_routeCount[i] << " tasks, "
                      << "avg latency " << avgRouteLatency << " s"
                      << std::endl;
        }
    }
    std::cout << "========================================\n" << std::endl;
}
