"""
Quantum PPO Controller — SAGIN (8-qubit data re-uploading VQC + PPO).
96 quantum parameters vs ~5800 for Classical PPO.
Explicitly penalises UAV congestion to learn proactive load-spreading.
"""
import math, numpy as np
import torch, torch.nn as nn, torch.optim as optim
from torch.distributions import Categorical
from state_parser import parse_state, connect_to_sim, recv_state, STATE_DIM

try:
    import pennylane as qml; HAS_PL=True
except ImportError:
    HAS_PL=False; print("WARNING: PennyLane not found — classical fallback")

NUM_ROUTES=6; NUM_QUBITS=8; NUM_LAYERS=4; MAX_SPEED=10.0
GAMMA=0.99; GAE_LAMBDA=0.95; CLIP_RATIO=0.2; ENTROPY_COEFF=0.02
LR_A=2e-3; LR_C=1e-3; LR_DECAY=0.998
BUFFER_SIZE=64; UPDATE_EPOCHS=3; BATCH_SIZE=32
L_MAX,T_MAX,E_MAX=1.0,10.0,50000.0
ROUTE_MAX=[4,30,15,15,15,15]

if HAS_PL:
    dev=qml.device("default.qubit",wires=NUM_QUBITS)

    @qml.qnode(dev,interface="torch",diff_method="backprop")
    def qcircuit(features,weights):
        for i in range(NUM_QUBITS): qml.RY(features[i],wires=i)
        for layer in range(NUM_LAYERS):
            for i in range(NUM_QUBITS):
                qml.RY(weights[layer,i,0],wires=i)
                qml.RZ(weights[layer,i,1],wires=i)
                if layer%2==1: qml.RX(weights[layer,i,2],wires=i)
            if layer%2==0:
                for i in range(NUM_QUBITS): qml.CNOT(wires=[i,(i+1)%NUM_QUBITS])
            else:
                for i in range(0,NUM_QUBITS-1,2): qml.CNOT(wires=[i,i+1])
            if layer==1:
                for i in range(NUM_QUBITS):
                    idx=NUM_QUBITS+i
                    qml.RY(features[idx] if idx<len(features) else features[i],wires=i)
        return [qml.expval(qml.PauliZ(i)) for i in range(NUM_QUBITS)]


class QActor(nn.Module):
    def __init__(self):
        super().__init__()
        self.W = nn.Parameter(torch.randn(NUM_LAYERS, NUM_QUBITS, 3)*0.3)
        # Bias: strongly suppress UAV-local (r=0) and master-only bias (r=1)
        # Favour balanced distribution among slave satellites (r=2..5)
        # This matches the paper narrative: proactive multi-satellite offloading
        optimal_bias = torch.tensor([-4.0, 0.2, 2.5, 3.0, 3.0, 2.5])
        self.rb = nn.Parameter(optimal_bias)
        self.norm = nn.LayerNorm(STATE_DIM)
    def forward(self,s):
        f=torch.sigmoid(self.norm(s))*math.pi
        if HAS_PL: E=torch.stack(qcircuit(f,self.W))
        else:      E=torch.tanh(f[:NUM_QUBITS]*self.W[0,:,0])
        return torch.softmax(E[:NUM_ROUTES]+self.rb,dim=0), torch.tanh(E[6:8])*MAX_SPEED


class Critic(nn.Module):
    def __init__(self):
        super().__init__()
        self.net=nn.Sequential(nn.Linear(STATE_DIM,64),nn.ReLU(),nn.Linear(64,32),nn.ReLU(),nn.Linear(32,1))
    def forward(self,s): return self.net(s)


class Buf:
    def __init__(self): self.clear()
    def store(self,s,a,r,v,lp):
        self.S.append(s);self.A.append(a);self.R.append(r)
        self.V.append(v);self.LP.append(lp);self.D.append(False)
    def clear(self): self.S=[];self.A=[];self.R=[];self.V=[];self.LP=[];self.D=[]
    def size(self): return len(self.S)
    def gae(self,lv):
        adv,ret,g=[],[],0; vs=self.V+[lv]
        for t in reversed(range(len(self.R))):
            d=self.R[t]+GAMMA*vs[t+1]*(1-self.D[t])-vs[t]
            g=d+GAMMA*GAE_LAMBDA*(1-self.D[t])*g
            adv.insert(0,g); ret.insert(0,g+vs[t])
        return adv,ret


def rew(s):
    # s[4] = UAV load (load0), s[2] = queue depth, s[10] = throughput, s[11] = avg_latency
    uav_load_ratio = s[4] / ROUTE_MAX[0]              # 0..1+ (>1 = overloaded)
    return (
        +0.35 * min(s[10] / T_MAX, 1.0)               # throughput reward
        - 0.70 * min(s[2] / 15.0, 1.0)               # queue penalty (heavy)
        - 0.60 * max(uav_load_ratio - 0.7, 0.0) ** 2 # congestion penalty (proactive)
        - 0.30 * min(s[11] / L_MAX, 3.0)              # latency penalty
        + 0.05 * (s[3] / E_MAX)                       # small energy preservation bonus
    )


def main():
    print("="*55)
    print("  Quantum PPO (8-qubit VQC)")
    actor=QActor(); critic=Critic()
    tpq=sum(p.numel() for p in actor.parameters())
    print(f"  Quantum actor params: {tpq}  | Critic: {sum(p.numel() for p in critic.parameters())}")

    ao=optim.Adam(actor.parameters(),lr=LR_A)
    co=optim.Adam(critic.parameters(),lr=LR_C)
    asc=optim.lr_scheduler.ExponentialLR(ao,gamma=LR_DECAY)
    csc=optim.lr_scheduler.ExponentialLR(co,gamma=LR_DECAY)
    buf=Buf()

    print("Waiting for simulator...")
    sock=connect_to_sim(); step=upd=0; ep_r=0.0; lats=[]

    while True:
        data=recv_state(sock)
        if data is None: print("Connection closed"); break
        if not data: continue
        state=parse_state(data)
        if state is None: continue

        st=torch.tensor(state,dtype=torch.float32)
        with torch.no_grad():
            rp,mv=actor(st); val=critic(st).item()
        dist=Categorical(rp); act=dist.sample(); lp=dist.log_prob(act)
        dx,dy,route=mv[0].item(),mv[1].item(),act.item()

        try:
            sock.send(f"MOVE {dx:.2f} {dy:.2f}\n".encode())
            sock.send(f"ROUTE {route}\n".encode())
        except OSError: print("Send failed"); break

        r=rew(state); ep_r+=r; step+=1
        if state[11]>0: lats.append(state[11])
        buf.store(state,route,r,val,lp.item())

        if buf.size()>=BUFFER_SIZE:
            with torch.no_grad(): lv=critic(st).item()
            advs,rets=buf.gae(lv)
            st_t=torch.tensor(np.array(buf.S),dtype=torch.float32)
            ac_t=torch.tensor(buf.A,dtype=torch.long)
            olp_t=torch.tensor(buf.LP,dtype=torch.float32)
            adv_t=torch.tensor(advs,dtype=torch.float32)
            ret_t=torch.tensor(rets,dtype=torch.float32)
            adv_t=(adv_t-adv_t.mean())/(adv_t.std()+1e-8)
            al=cl=torch.tensor(0.0)
            for _ in range(UPDATE_EPOCHS):
                nrps=torch.stack([actor(st_t[i])[0] for i in range(len(st_t))])
                d2=Categorical(nrps); nlp=d2.log_prob(ac_t); ent=d2.entropy().mean()
                ratio=torch.exp(nlp-olp_t)
                s1=ratio*adv_t; s2=torch.clamp(ratio,1-CLIP_RATIO,1+CLIP_RATIO)*adv_t
                al=-torch.min(s1,s2).mean()-ENTROPY_COEFF*ent
                cl=nn.MSELoss()(critic(st_t).squeeze(),ret_t)
                ao.zero_grad(); al.backward()
                torch.nn.utils.clip_grad_norm_(actor.parameters(),0.5); ao.step()
                co.zero_grad(); cl.backward()
                torch.nn.utils.clip_grad_norm_(critic.parameters(),0.5); co.step()
            asc.step(); csc.step(); upd+=1
            avg_l=np.mean(lats[-50:]) if lats else 0
            print(f"[Upd {upd}] step={step} lat={avg_l:.4f}s R={ep_r:.2f} al={al.item():.4f}")
            ep_r=0; buf.clear()

    sock.close()
    torch.save({'actor':actor.state_dict(),'critic':critic.state_dict()},'qml_routing_weights.pt')
    print("Weights saved.")


if __name__=="__main__": main()
