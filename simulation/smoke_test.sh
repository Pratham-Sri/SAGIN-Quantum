#!/bin/bash
# Quick smoke test: run controller_random for 30s to confirm the pipeline works
NS3=/home/pratham/ns-allinone-3.41/ns-3.41
SIM_DIR=$NS3/scratch/sagin-sim
SIM_TIME=30
PYTHON=python3
if [ -d "$SIM_DIR/rl_env/bin" ]; then PYTHON="$SIM_DIR/rl_env/bin/python3"; fi

echo "=== Smoke test: controller_random for ${SIM_TIME}s ==="

pkill -9 -f "ns3.41-sagin-main" 2>/dev/null || true
fuser -k 9001/tcp 2>/dev/null || true
sleep 2
rm -f "$NS3/sagin_metrics.csv"

cd "$NS3"
./ns3 run "scratch/sagin-sim/sagin-main --simTime=${SIM_TIME}" > /tmp/smoke_sim.log 2>&1 &
SIM_PID=$!

echo "Waiting for port 9001..."
for i in $(seq 1 15); do
    sleep 1
    if ss -tlnp 2>/dev/null | grep -q ':9001'; then echo "Port ready (${i}s)"; break; fi
done

cd "$SIM_DIR"
timeout $((SIM_TIME + 15)) $PYTHON controller_random.py > /tmp/smoke_ctrl.log 2>&1 || true
wait $SIM_PID 2>/dev/null || true

echo ""
echo "=== Simulation summary ==="
grep -E "Tasks completed|Average latency|Deadline|success rate" /tmp/smoke_sim.log || echo "(no summary found)"
echo ""
echo "=== CSV check ==="
if [ -f "$NS3/sagin_metrics.csv" ]; then
    ROWS=$(awk 'NR>1' "$NS3/sagin_metrics.csv" | wc -l)
    echo "sagin_metrics.csv: $ROWS rows"
    echo "First 5 data rows:"
    head -6 "$NS3/sagin_metrics.csv"
else
    echo "ERROR: No CSV produced!"
    echo "Sim log tail:"
    tail -15 /tmp/smoke_sim.log
fi
echo ""
echo "=== Controller log tail ==="
tail -10 /tmp/smoke_ctrl.log
