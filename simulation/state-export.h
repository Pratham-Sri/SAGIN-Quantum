#ifndef STATE_EXPORT_H
#define STATE_EXPORT_H

#include "topology.h"
#include "task-queue.h"
#include "control-interface.h"
#include "metrics.h"
#include "energy-model.h"
#include "offloading-engine.h"

class StateExport
{

public:

    StateExport();

    void SetQueue(TaskQueue *queue);
    void SetController(ControlInterface *controller);
    void SetMetrics(Metrics *metrics);
    void SetEnergyModel(EnergyModel *energy);
    void SetOffloadingEngine(OffloadingEngine *engine);

    void SendState(SaginTopology &topo);

private:

    TaskQueue *m_queue;
    ControlInterface *m_controller;
    Metrics *m_metrics;
    EnergyModel *m_energy;
    OffloadingEngine *m_engine;
};

#endif
