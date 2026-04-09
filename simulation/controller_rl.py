"""
Tabular Q-Learning Controller — SAGIN baseline.
"""
import random, numpy as np
from state_parser import parse_state, connect_to_sim, recv_state

L_MAX,T_MAX,E_MAX=1.0,10.0,50000.0
ROUTE_MAX=[4,30,15,15,15,15]
ACTIONS=[(dx,dy,r) for r in range(6) for dx,dy in [(-5,0),(5,0),(0,5),(0,-5)]]

def disc(s):
    return (min(int(s[0]/200),4), min(int(s[1]/200),4),
            min(int(s[2]/5),4),  min(int(s[4]/2),4))

qt={}; EPS,ALPHA,GAMMA=0.5,0.15,0.95
def gq(sk,ai): return qt.get((sk,ai), -50.0)
def sq(sk,ai,v): qt[(sk,ai)]=v
def choose(sk):
    return (random.randrange(len(ACTIONS)) if random.random()<EPS
            else max(range(len(ACTIONS)),key=lambda a:gq(sk,a)))

def rew(s):
    return (-0.5*min(s[11]/L_MAX,3.0)+0.3*min(s[10]/T_MAX,1.0)
            -0.4*max(s[4]/ROUTE_MAX[0]-1.0,0.0)**2-0.1*min(s[2]/20.0,1.0))

print("Q-Learning Controller — Waiting for simulator...")
sock=connect_to_sim(); psk=pai=None; step=0

while True:
    data=recv_state(sock)
    if data is None: print("Connection closed"); break
    if not data: continue
    state=parse_state(data)
    if state is None: continue
    sk=disc(state); r=rew(state)
    if psk is not None:
        old=gq(psk,pai); mxq=max(gq(sk,a) for a in range(len(ACTIONS)))
        sq(psk,pai, old+ALPHA*(r+GAMMA*mxq-old))
    ai=choose(sk)
    dx,dy,route=ACTIONS[ai]
    try:
        sock.send(f"MOVE {dx} {dy}\n".encode())
        sock.send(f"ROUTE {route}\n".encode())
    except OSError: break
    psk=sk; pai=ai; step+=1
    if step%20==0:
        print(f"[Step {step}] Qt={len(qt)} r={r:.3f} uav={int(state[4])} →r{route}")

sock.close()
print(f"Done. Q-table: {len(qt)} entries")
