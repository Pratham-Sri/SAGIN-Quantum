#ifndef METRICS_H
#define METRICS_H

#include "task-queue.h"
#include <fstream>

class Metrics
{

public:

    Metrics();
    ~Metrics();

    /* Log a completed task with latency and route info */
    void LogTaskCompletion(double time, double latency,
                          int routeId, bool deadlineMet);

    /* Log full system state (called every timestep) */
    void LogState(
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
        bool deadlineMet);

    /* Compute latency for a task (returns latency value) */
    double ComputeLatency(Task task);

    void LogQueueSize(int size);

    /* Throughput tracking */
    void RecordTaskCompletion(double dataSize);
    double GetThroughputTasks() const;
    double GetThroughputBits() const;
    double GetAverageLatency() const;
    int GetDeadlinesMet() const;
    int GetDeadlinesMissed() const;

    void PrintSummary();

private:

    std::ofstream logfile;

    double totalLatency;
    int tasksCompleted;

    /* Throughput tracking */
    double m_windowStart;
    int m_tasksInWindow;
    double m_bitsInWindow;
    double m_throughputTasks;
    double m_throughputBits;

    /* Deadline tracking */
    int m_deadlinesMet;
    int m_deadlinesMissed;

    /* Per-route stats */
    int m_routeCount[6];
    double m_routeLatency[6];

    /* Cached last-known state values for task-completion CSV rows */
    double m_lastX;
    double m_lastY;
    int    m_lastQueueSize;
    double m_lastEnergy;
    double m_lastLoad[6];
};

#endif
