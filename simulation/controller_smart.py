"""
Smart Greedy Controller — myopic baseline.
Routes to lowest-latency node given CURRENT loads.
Over-saturates UAV when loads are stale; no look-ahead.
"""
from state_parser import parse_state, connect_to_sim, recv_state

CENTER_X,CENTER_Y=500.0,500.0; MAX_SPEED=8.0
BASE_LAT=[0.003,0.042,0.057,0.057,0.057,0.057]
MAX_LOAD=[4,30,15,15,15,15]
PENALTY =[0.08,0.01,0.01,0.01,0.01,0.01]

def est_lat(r,load):
    ov=load-MAX_LOAD[r]
    return BASE_LAT[r]+(PENALTY[r]*ov*ov if ov>0 else load*0.005)

print("Smart Greedy Controller — Waiting for simulator...")
sock=connect_to_sim(); step=0

while True:
    data=recv_state(sock)
    if data is None: print("Connection closed"); break
    if not data: continue
    state=parse_state(data)
    if state is None: continue
    x,y,queue=state[0],state[1],state[2]
    loads=state[4:10]; step+=1
    dx=max(min((CENTER_X-x)*0.04,MAX_SPEED),-MAX_SPEED)
    dy=max(min((CENTER_Y-y)*0.04,MAX_SPEED),-MAX_SPEED)
    try: sock.send(f"MOVE {dx:.2f} {dy:.2f}\n".encode())
    except OSError: break
    best_r=min(range(6),key=lambda r:est_lat(r,loads[r]))
    try: sock.send(f"ROUTE {best_r}\n".encode())
    except OSError: break
    if step%10==0:
        print(f"[Step {step}] q={int(queue)} uav={int(loads[0])}/{MAX_LOAD[0]} →r{best_r}")

sock.close()
