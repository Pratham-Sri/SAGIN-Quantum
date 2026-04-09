#!/bin/bash
cd ~/ns-allinone-3.41/ns-3.41
./ns3 run 'scratch/sagin-sim/sagin-main --simTime=5' > /tmp/state_sample.txt 2>&1 &
sleep 3
cd scratch/sagin-sim
source rl_env/bin/activate
python3 << 'PYEOF'
import socket, time
s = socket.socket()
s.connect(('127.0.0.1', 9001))
d = s.recv(4096).decode()
print("RAW STATE:", repr(d))
parts = d.strip().split("\n")
for p in parts:
    if p.startswith("STATE"):
        print("FIELDS:", p.split())
        print("FIELD COUNT:", len(p.split()))
s.close()
PYEOF
wait
