#!/bin/bash
SIM=/home/pratham/ns-allinone-3.41/ns-3.41/scratch/sagin-sim
SRC=/mnt/c/Users/Pratham/VS_Dump/sagin_tmp

echo "=== Copying updated source files ==="
cp "$SRC/offloading-engine.cc"       "$SIM/"
cp "$SRC/offloading-engine.h"        "$SIM/"
cp "$SRC/metrics.cc"                 "$SIM/"
cp "$SRC/metrics.h"                  "$SIM/"
cp "$SRC/controller_qml_routing.py"  "$SIM/"
cp "$SRC/controller_qrl.py"          "$SIM/"
cp "$SRC/controller_random.py"       "$SIM/"
cp "$SRC/controller_smart.py"        "$SIM/"
cp "$SRC/controller_rl.py"           "$SIM/"
cp "$SRC/controller_drl.py"          "$SIM/"
cp "$SRC/state_parser.py"            "$SIM/"
cp "$SRC/plot_results.py"            "$SIM/"
echo "=== Files copied ==="
ls -la "$SIM/metrics.cc" "$SIM/controller_qrl.py"
