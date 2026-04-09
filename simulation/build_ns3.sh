#!/bin/bash
set -e
NS3=/home/pratham/ns-allinone-3.41/ns-3.41
echo "=== Building ns-3 SAGIN ==="
cd "$NS3"
./ns3 build scratch/sagin-sim/sagin-main 2>&1
echo "=== Build done ==="
