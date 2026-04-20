# Quantum Proximal Policy Optimization (QPPO) for 6G SAGIN

Welcome to the open-source repository for our high-fidelity **Space-Air-Ground Integrated Network (SAGIN)** task offloading simulator. This project tackles the NP-hard problem of dynamic Mobile Edge Computing (MEC) load balancing for Unmanned Aerial Vehicles (UAVs) using a globally sparse, highly constrained Low-Earth Orbit (LEO) satellite backhaul.

This repository pairs an industry-standard **C++ ns-3 discrete packet-level network simulator** with a cutting edge **Quantum Machine Learning (QML)** inference engine written in Python (PennyLane/TorchQuantum). 

## 🚀 Key Academic Improvements
This methodology isolates and empirically resolves severe limitations found in the foundational Quantum Actor-Critic networking literature, primarily extending over the QEA2C heuristic bounds introduced in "*Quantum DRL for Green UAV Positioning in 6G-Enabled SAGIN*" (Sasinda et al., IEEE Globecom 2025). 

We introduce three major systemic transformations:
1. **Monotonic Flight Bounds via QPPO:** We replaced unconstrained Actor-Critic structures with clipped Proximal Policy Optimization, completely halting catastrophic forgetting and destructive coordinate routing observed in basic QML implementations.
2. **Data Re-uploading VQC (Extreme Parameter Shrinkage):** Rather than limiting feature-maps to static Amplitude Encoding (AE) matrices, our model cyclically interleaves continuous geometric distance features repetitively through 8 core qubits. This establishes immense continuous-function approximation power using only **96 trained variables** (substantially outclassing the 5000+ variables traditionally found in DRL environments).
3. **Proactive Queue-Shedding Reward Logic:** Instead of penalizing models *after* latency times out, our Python matrix reads exact hardware queuing FIFO layers streaming directly from the asynchronous `ns-3` TCP socket. The agent detects payload saturation mathematically before it cascades, preemptively scattering payloads evenly across LEO Slave-Nano-Satellites.

## 📂 Repository Structure

```text
📦 SAGIN-Quantum
 ┣ 📂 simulation             # Core network simulator and Reinforcement Learning matrix
 ┃ ┣ 📜 run_all.sh           # Main execution wrapper linking Python to ns-3
 ┃ ┣ 📜 plot_results.py      # Seaborn visualization script for metric validation
 ┃ ┣ 📜 sagin-main.cc        # ns-3 C++ Topology Environment and TCP Socket interface
 ┃ ┣ 📜 controller_qml_routing.py # Proposed QPPO implementation (TorchQuantum/PennyLane)
 ┃ ┣ 📜 controller_qrl.py    # Paper Baseline algorithm (QEA2C)
 ┃ ┗ ... (Classical DRL, Smart heuristics, and Tabular RL algorithms)
 ┣ 📂 visualizer             # Frontend 3D dynamic web dashboard rendering SAGIN telemetry
 ┗ 📂 paper                  # The formal drafted IEEE double-column LaTeX manuscript (.tex)
```

## 📊 Empirical Validations
By benchmarking our localized QPPO controller specifically against classical heuristics and the direct 2025 QEA2C framework baseline, the algorithm yielded definitive statistical dominance mapping native physical packet-layer interference:

* **Latency:** End-to-end task turnaround was driven down natively to **0.0779 seconds** (a ~16x improvement over the QEA2C baseline of 1.254 seconds).
* **Reliability:** Operational tracking hit **100% completion rates** satisfying strict 6G URLLC execution delivery bounds.

## ⚙️ How to Test and Run
This structure natively requires an underlying Unix (or WSL) runtime equipped with `ns-3.41` installations correctly configured. 
1. Install Python prerequisites inside your simulation environment: `pip install torch pennylane pandas seaborn matplotlib`
2. Run the fully automated simulation suite spanning all specific controllers natively:
   ```bash
   cd simulation
   bash run_all.sh
   ```
3. Allow the `ns-3` engine to finish parallel batch processing. Once executed, the analytical tracking engine captures output states into CSV records.
4. Extract visual inference limits by running the validation plotter locally:
   ```bash
   python plot_results.py
   ```
Generated verification data points will map instantly matching graphs found directly integrated mathematically alongside the analytical `paper/sagin_research_paper.tex` repository literature.
