#ifndef OFFLOADING_ENGINE_H
#define OFFLOADING_ENGINE_H

#include "task-queue.h"

/* Route IDs:
   0 = UAV local processing  (fast but limited capacity)
   1 = Master satellite      (high capacity, 40ms extra latency)
   2 = Slave satellite 0     (medium capacity, 55ms extra)
   3 = Slave satellite 1
   4 = Slave satellite 2
   5 = Slave satellite 3 */

#define NUM_ROUTES 6

class OffloadingEngine
{
public:

    OffloadingEngine();

    /* Process a task on the specified route; returns estimated latency */
    double Process(Task task, int routeId);

    /* Current load (task count) on a node */
    double GetNodeLoad(int nodeId) const;

    /* Load ratio: currentLoad / maxLoad  (0.0 → 1.0+) */
    double GetNodeLoadRatio(int nodeId) const;

    /* Estimated latency for a route under current load */
    double GetRouteLatency(int routeId) const;

    /* Decrement load when a task finishes */
    void TaskCompleted(int routeId);

    /* Compute capacity in GHz */
    double GetComputeCapacity(int nodeId) const;

private:

    double m_computeCapacity[NUM_ROUTES];
    int    m_currentLoad[NUM_ROUTES];
    int    m_maxLoad[NUM_ROUTES];      // congestion threshold per node
    double m_commLatency[NUM_ROUTES];
};

#endif
