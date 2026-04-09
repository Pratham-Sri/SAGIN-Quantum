#include "energy-model.h"

#include <iostream>
#include <cmath>

EnergyModel::EnergyModel()
{
    m_initialEnergy = 50000.0;   // 50 kJ — realistic for UAV battery
    m_energy = m_initialEnergy;
    m_totalConsumed = 0.0;
}

void EnergyModel::ConsumeFlight(double speed)
{
    if(m_energy <= 0) return;

    /* Simplified rotary-wing UAV power model:
       Scaled down for simulation timesteps.
       P(V) = P_blade(1 + 3V^2/V_tip^2) + P_induced/(1+V) + P_parasite*V^3
       Energy per timestep (1 second) */

    double power;

    if(speed < 0.1)
    {
        /* hovering power ~ 168 W */
        power = P_BLADE + P_INDUCED;
    }
    else
    {
        power = P_BLADE * (1.0 + 3.0 * speed * speed / (V_TIP * V_TIP))
              + P_INDUCED / (1.0 + speed)
              + P_PARASITE * speed * speed * speed;
    }

    /* Scale: energy per second = power (Watts = J/s) */
    double e = power * 1.0;

    m_energy -= e;
    m_totalConsumed += e;

    if(m_energy < 0) m_energy = 0;
}

void EnergyModel::ConsumeCompute(double cpuCycles)
{
    if(m_energy <= 0) return;

    /* Energy = kappa * cpuCycles
       kappa = 1e-7 J/cycle (realistic for edge processor) */
    double e = cpuCycles * 1e-7;

    m_energy -= e;
    m_totalConsumed += e;

    if(m_energy < 0) m_energy = 0;
}

void EnergyModel::ConsumeTransmit(double dataSize)
{
    if(m_energy <= 0) return;

    /* Transmission energy: P_tx * (dataSize / dataRate) */
    double dataRate = 54e6; // 54 Mbps WiFi
    double txTime = dataSize / dataRate;
    double e = TX_POWER * txTime;

    m_energy -= e;
    m_totalConsumed += e;

    if(m_energy < 0) m_energy = 0;
}

double EnergyModel::GetEnergy() const
{
    return m_energy;
}

double EnergyModel::GetTotalConsumed() const
{
    return m_totalConsumed;
}

bool EnergyModel::IsAlive() const
{
    return m_energy > 0;
}

void EnergyModel::Reset()
{
    m_energy = m_initialEnergy;
    m_totalConsumed = 0.0;
}
