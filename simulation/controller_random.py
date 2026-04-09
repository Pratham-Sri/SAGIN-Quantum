"""
Random Controller — lowest baseline.
"""
import random
from state_parser import parse_state, connect_to_sim, recv_state

MAX_SPEED=10.0
print("Random Controller — Waiting for simulator...")
sock=connect_to_sim(); step=0

while True:
    data=recv_state(sock)
    if data is None: print("Connection closed"); break
    if not data: continue
    state=parse_state(data)
    if state is None: continue
    step+=1
    dx=random.uniform(-MAX_SPEED,MAX_SPEED)
    dy=random.uniform(-MAX_SPEED,MAX_SPEED)
    route=random.randint(0,5)
    try:
        sock.send(f"MOVE {dx:.2f} {dy:.2f}\n".encode())
        sock.send(f"ROUTE {route}\n".encode())
    except OSError: break
    if step%10==0:
        print(f"[Step {step}] t={state[14]:.0f} q={int(state[2])} uav={int(state[4])} →r{route}")

sock.close()
