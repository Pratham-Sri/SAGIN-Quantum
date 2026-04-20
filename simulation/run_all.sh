#!/bin/bash
# =============================================================================
#  SAGIN Full Comparison Run — All 6 Controllers
#  Quantum PPO vs QEA2C vs Classical baselines
#  Usage: bash run_all.sh
#  Run from: ~/ns-allinone-3.41/ns-3.41/scratch/sagin-sim/
# =============================================================================

set -e

# ── Paths ─────────────────────────────────────────────────────────────────────
NS3="${HOME}/ns-allinone-3.41/ns-3.41"
SIM_DIR="${NS3}/scratch/sagin-sim"
RESULTS="${SIM_DIR}/results"
SIM_TIME=100                 # Simulation duration in seconds
PYTHON="python3"             # Use venv python if needed: SIM_DIR/rl_env/bin/python3
mkdir -p "${RESULTS}"

FORCE_RUN=0
if [ "$1" == "--force-simulate" ]; then
    FORCE_RUN=1
fi

if [ $FORCE_RUN -eq 0 ]; then
    echo ""
    echo "========================================================================="
    echo "  Notice: ns-3 multi-satellite discrete-event simulation routines disabled"
    echo "          by default to bypass heavy CPU allocation blocks."
    echo "  Action: Plotting finalized outcomes directly from results/."
    echo "          (To run full packet-level physics engine: bash run_all.sh --force-simulate)"
    echo "========================================================================="
    echo ""
    echo "Generating evaluation graphs..."
    python3 plot_results.py
    echo "Graphs updated in plots/ directory."
    exit 0
fi

# ── Controllers to benchmark ──────────────────────────────────────────────────
CONTROLLERS=(
    "controller_random"
    "controller_smart"
    "controller_rl"
    "controller_drl"
    "controller_qrl"
    "controller_qml_routing"
)

declare -A RES_TASKS RES_LAT RES_DEAD RES_TPUT

# ── Build the simulation first ────────────────────────────────────────────────
echo ""
echo "=============================================="
echo "  Building ns-3 SAGIN simulation..."
echo "=============================================="
cd "${NS3}"
./ns3 build scratch/sagin-sim/sagin-main 2>&1 | tail -5
echo "Build complete."

# ── Run each controller ───────────────────────────────────────────────────────
for CTRL in "${CONTROLLERS[@]}"; do
    echo ""
    echo "=============================================="
    echo "  Running: ${CTRL}  (simTime=${SIM_TIME}s)"
    echo "=============================================="

    # Kill any lingering processes from prior run
    pkill -9 -f "ns3.*sagin-main" 2>/dev/null || true
    pkill -9 -f "${CTRL}.py"      2>/dev/null || true
    fuser -k 9001/tcp             2>/dev/null || true
    sleep 2

    # Remove stale CSV
    rm -f "${NS3}/sagin_metrics.csv"

    # Start ns-3 simulation in background
    cd "${NS3}"
    ./ns3 run "scratch/sagin-sim/sagin-main --simTime=${SIM_TIME}" \
        > "/tmp/sim_${CTRL}.log" 2>&1 &
    SIM_PID=$!

    # Wait for it to open the TCP socket
    echo "  Waiting for simulator to bind port 9001..."
    for i in $(seq 1 15); do
        sleep 1
        if fuser 9001/tcp >/dev/null 2>&1; then
            echo "  Port 9001 ready (${i}s)"
            break
        fi
    done

    # Start the Python controller (timeout = simTime + 20s grace)
    cd "${SIM_DIR}"
    timeout $((SIM_TIME + 20)) ${PYTHON} "${CTRL}.py" \
        > "/tmp/ctrl_${CTRL}.log" 2>&1 || true

    wait ${SIM_PID} 2>/dev/null || true

    # Save CSV results
    CSV_SRC="${NS3}/sagin_metrics.csv"
    CSV_DST="${RESULTS}/results_${CTRL}.csv"

    if [ -f "${CSV_SRC}" ]; then
        cp "${CSV_SRC}" "${CSV_DST}"
        ROWS=$(wc -l < "${CSV_DST}")
        echo "  CSV saved → ${CSV_DST}  (${ROWS} data rows)"
    else
        echo "  WARNING: No CSV produced — check /tmp/sim_${CTRL}.log"
    fi

    # Extract summary from sim log
    LOG="/tmp/sim_${CTRL}.log"
    RES_TASKS[${CTRL}]=$(grep "Tasks completed"     "${LOG}" 2>/dev/null | grep -oP '\d+' | tail -1)
    RES_LAT[${CTRL}]=$(  grep "Average latency"     "${LOG}" 2>/dev/null | grep -oP '[0-9.]+' | tail -1)
    RES_DEAD[${CTRL}]=$( grep "Deadline success"    "${LOG}" 2>/dev/null | grep -oP '[0-9.]+' | tail -1)
    RES_TPUT[${CTRL}]=$( grep "Throughput:"        "${LOG}" 2>/dev/null | grep -oP '[0-9.]+' | head -1)

    echo "  Tasks=${RES_TASKS[${CTRL}]:-N/A}  Lat=${RES_LAT[${CTRL}]:-N/A}s  Dead=${RES_DEAD[${CTRL}]:-N/A}%"
done

# ── Final comparison table ────────────────────────────────────────────────────
echo ""
echo "=============================================================="
echo "                 FINAL COMPARISON TABLE"
echo "=============================================================="
printf "%-26s %8s %10s %10s %10s\n" \
    "Controller" "Tasks" "Latency(s)" "Thruput" "Deadline%"
printf "%-26s %8s %10s %10s %10s\n" \
    "──────────────────────────" "─────" "──────────" "───────" "─────────"
for CTRL in "${CONTROLLERS[@]}"; do
    printf "%-26s %8s %10s %10s %10s\n" \
        "${CTRL}" \
        "${RES_TASKS[${CTRL}]:-N/A}" \
        "${RES_LAT[${CTRL}]:-N/A}" \
        "${RES_TPUT[${CTRL}]:-N/A}" \
        "${RES_DEAD[${CTRL}]:-N/A}"
done
echo "=============================================================="
echo ""
echo "CSVs saved to: ${RESULTS}/"
echo ""
echo "To generate graphs, run from sagin-sim/:"
echo "  python3 plot_results.py"
