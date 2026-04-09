#ifndef ENERGY_MODEL_H
#define ENERGY_MODEL_H

class EnergyModel
{

public:

    EnergyModel();

    /* Flight energy: simplified rotary-wing UAV power model */
    void ConsumeFlight(double speed);

    /* Compute energy for local task processing */
    void ConsumeCompute(double cpuCycles);

    /* Transmission energy for offloading */
    void ConsumeTransmit(double dataSize);

    /* Getters */
    double GetEnergy() const;
    double GetTotalConsumed() const;
    bool IsAlive() const;

    /* Reset for new episode */
    void Reset();

private:

    double m_energy;
    double m_initialEnergy;
    double m_totalConsumed;

    /* UAV power model parameters */
    static constexpr double P_BLADE    = 79.86;   // blade profile power (W)
    static constexpr double P_INDUCED  = 88.63;   // induced power (W)
    static constexpr double P_PARASITE = 0.0045;   // parasite drag coefficient
    static constexpr double V_TIP     = 120.0;    // rotor tip speed (m/s)
    static constexpr double KAPPA     = 0.001;    // energy per CPU cycle (J/cycle)
    static constexpr double TX_POWER  = 0.5;      // transmit power (W)

};

#endif
