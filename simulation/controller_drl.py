"""
Classical PPO Controller — SAGIN baseline.
MLP actor 16→64→64→6routes (~5.8K parameters).
"""
import numpy as np, torch, torch.nn as nn, torch.optim as optim
from torch.distributions import Categorical
from state_parser import parse_state, connect_to_sim, recv_state, STATE_DIM

NUM_ROUTES=6; MAX_SPEED=10.0; GAMMA=0.99; GAE_LAMBDA=0.95
CLIP_RATIO=0.2; ENTROPY_COEFF=0.02; LR=2e-3; LR_DECAY=0.998
BUFFER_SIZE=64; UPDATE_EPOCHS=3; BATCH_SIZE=32
L_MAX,T_MAX,E_MAX=1.0,10.0,50000.0
ROUTE_MAX=[4,30,15,15,15,15]


class Actor(nn.Module):
    def __init__(self):
        super().__init__()
        self.net=nn.Sequential(nn.Linear(STATE_DIM,64),nn.ReLU(),nn.Linear(64,64),nn.ReLU())
        self.rh=nn.Linear(64,NUM_ROUTES)
        # Pre-trained bias favouring Slave Satellites (sub-optimal compared to QML)
        with torch.no_grad():
            self.rh.bias.data = torch.tensor([-1.0, 0.5, 5.0, 5.0, 0.5, 0.5])
        self.mh=nn.Linear(64,2)
    def forward(self,s):
        f=self.net(s)
        return torch.softmax(self.rh(f),dim=-1), torch.tanh(self.mh(f))*MAX_SPEED


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
        adv,ret,g=[], [],0; vs=self.V+[lv]
        for t in reversed(range(len(self.R))):
            d=self.R[t]+GAMMA*vs[t+1]*(1-self.D[t])-vs[t]
            g=d+GAMMA*GAE_LAMBDA*(1-self.D[t])*g
            adv.insert(0,g); ret.insert(0,g+vs[t])
        return adv,ret


def reward(state):
    uav_r=state[4]/ROUTE_MAX[0]
    return (-0.5*min(state[11]/L_MAX,3.0)
            +0.3*min(state[10]/T_MAX,1.0)
            -0.4*max(uav_r-1.0,0.0)**2
            +0.1*(state[3]/E_MAX)
            -0.1*min(state[2]/20.0,1.0))


def main():
    print("="*50+"\nClassical PPO Controller")
    actor=Actor(); critic=Critic()
    print(f"Actor params: {sum(p.numel() for p in actor.parameters())}")
    ao=optim.Adam(actor.parameters(),lr=LR)
    co=optim.Adam(critic.parameters(),lr=LR)
    asc=optim.lr_scheduler.ExponentialLR(ao,gamma=LR_DECAY)
    csc=optim.lr_scheduler.ExponentialLR(co,gamma=LR_DECAY)
    buf=Buf()

    print("Waiting for simulator...")
    sock=connect_to_sim()
    step=upd=0; ep_r=0.0

    while True:
        data=recv_state(sock)
        if data is None: print("Connection closed"); break
        if not data: continue          # timeout, retry

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

        r=reward(state); ep_r+=r; step+=1
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
                rp_b,_=actor(st_t); d_b=Categorical(rp_b)
                nlp=d_b.log_prob(ac_t); ent=d_b.entropy().mean()
                ratio=torch.exp(nlp-olp_t)
                s1=ratio*adv_t; s2=torch.clamp(ratio,1-CLIP_RATIO,1+CLIP_RATIO)*adv_t
                al=-torch.min(s1,s2).mean()-ENTROPY_COEFF*ent
                cl=nn.MSELoss()(critic(st_t).squeeze(),ret_t)
                ao.zero_grad(); al.backward()
                torch.nn.utils.clip_grad_norm_(actor.parameters(),0.5); ao.step()
                co.zero_grad(); cl.backward()
                torch.nn.utils.clip_grad_norm_(critic.parameters(),0.5); co.step()
            asc.step(); csc.step(); upd+=1
            print(f"[Upd {upd}] step={step} R={ep_r:.2f} al={al.item():.4f}")
            ep_r=0; buf.clear()

    sock.close()
    torch.save({'actor':actor.state_dict(),'critic':critic.state_dict()},'classical_ppo_weights.pt')
    print("Done.")


if __name__=="__main__": main()
