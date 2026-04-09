import { useState, useEffect } from 'react';
import { Activity, Clock, Zap, Cpu, Orbit, TerminalSquare, Radio } from 'lucide-react';
import GlobeSim from './components/GlobeSim';

function App() {
  const [activeTask, setActiveTask] = useState({});
  const [activeAlgo, setActiveAlgo] = useState('Waiting for Telemetry...');
  const [isConnected, setIsConnected] = useState(false);

  // Connect to Live Telemetry WebSocket
  useEffect(() => {
    let ws;
    const connectWS = () => {
      ws = new WebSocket("ws://localhost:8080");
      
      ws.onopen = () => {
        setIsConnected(true);
      };
      
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          setActiveTask(data);
          setActiveAlgo(data.algo === 'qml' ? "QPPO (Proposed)" : "QEA2C (Baseline)");
        } catch (e) {
          console.error("Invalid Telemetry", e);
        }
      };
      
      ws.onclose = () => {
        setIsConnected(false);
        // Try to reconnect every 2s
        setTimeout(connectWS, 2000);
      };
      
      ws.onerror = (err) => {
        ws.close();
      }
    };
    
    connectWS();
    
    return () => {
        if(ws) ws.close();
    }
  }, []);

  // Aggregate Metrics over time (just read the JSON broadcast)
  const currentLatency = activeTask.latency ? activeTask.latency.toFixed(3) : "0.000";
  const currentQ = activeTask.queue || 0;
  const currentEnergy = activeTask.energy ? Math.round(activeTask.energy) : 50000;
  const currentTput = activeTask.throughput_tasks ? activeTask.throughput_tasks.toFixed(1) : "0.0";

  return (
    <div className="w-full h-screen bg-[#050511] text-white flex overflow-hidden font-sans selection:bg-blue-500/30">
      
      {/* LEFT SIDEBAR: Metrics & Controls */}
      <div className="w-96 border-r border-white/10 bg-[#0a0a1a] flex flex-col relative z-10 shadow-2xl">
        <div className="p-6 border-b border-white/10">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-3">
               <Orbit className="w-8 h-8 text-blue-500" />
               <h1 className="text-2xl font-bold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-emerald-400">
                 SAGIN Command
               </h1>
            </div>
            {/* Live Indicator */}
            <div className="flex flex-col items-end">
                <div className={`flex items-center gap-2 px-2 py-1 rounded border ${
                    isConnected ? 'bg-green-500/10 border-green-500/30 text-green-400' 
                                : 'bg-red-500/10 border-red-500/30 text-red-400'
                }`}>
                    <Radio className={`w-3 h-3 ${isConnected ? 'animate-pulse' : ''}`} />
                    <span className="text-[10px] font-bold uppercase tracking-wider">
                        {isConnected ? 'Live Telemetry' : 'Disconnected'}
                    </span>
                </div>
            </div>
          </div>
          <p className="text-gray-400 text-sm">Real-time ns-3 Engine Connection</p>
        </div>

        {/* Algorithm Toggle (Now Display Only) */}
        <div className="p-6 border-b border-white/10">
          <h2 className="text-xs uppercase tracking-wider text-gray-500 font-semibold mb-4">Active Controller Node</h2>
          <div className="flex bg-[#121226] p-4 rounded-lg items-center justify-center border border-white/5">
            <span className={`text-lg font-bold ${activeAlgo.includes('QPPO') ? 'text-blue-400' : activeAlgo.includes('QEA2C') ? 'text-red-400' : 'text-gray-400 animate-pulse'}`}>
                {activeAlgo}
            </span>
          </div>
          <p className="text-xs text-gray-500 mt-3">
            {activeAlgo.includes('QPPO') 
              ? "Receiving UDP broadcasts via ns-3 interface. QPPO balances among Slave Sats."
              : activeAlgo.includes('QEA2C') ? "Receiving UDP broadcasts via ns-3 interface. QEA2C heavily biases Master Sat." : "Awaiting Python engine execution..."}
          </p>
        </div>

        {/* Live Metrics */}
        <div className="p-6 flex-1 overflow-y-auto">
          <h2 className="text-xs uppercase tracking-wider text-gray-500 font-semibold mb-4">Live State Telemetry</h2>
          
          <div className="grid gap-4">
            <MetricCard icon={<Clock />} label="Current Latency" value={`${currentLatency} s`} color="text-yellow-400" />
            <MetricCard icon={<Activity />} label="Throughput" value={`${currentTput} t/s`} color="text-emerald-400" />
            <MetricCard icon={<TerminalSquare />} label="UAV Queue Depth" value={`${currentQ} pkts`} color="text-orange-400" />
            <MetricCard icon={<Zap />} label="Energy Reserve" value={`${currentEnergy} J`} color="text-cyan-400" />
            
            {/* Active Route Focus */}
            <div className={`p-4 rounded-xl border mt-4 transition-all ${activeTask.route !== undefined ? 'bg-white/5 border-white/10' : 'bg-transparent border-transparent opacity-50'}`}>
              <div className="flex items-center gap-2 mb-2">
                <Cpu className="w-4 h-4 text-gray-400" />
                <span className="text-sm font-medium text-gray-300">Last Routed Packet Target</span>
              </div>
              <div className="text-2xl font-bold flex items-center justify-between">
                <span>{activeTask.route === undefined ? '—' : activeTask.route === 1 ? 'Master Satellite' : activeTask.route === 0 ? 'Local Compute' : `Slave Satellite ${activeTask.route - 2}`}</span>
                {activeTask.route !== undefined && (
                    <span className={`w-3 h-3 rounded-full animate-pulse ${activeTask.route === 1 ? 'bg-red-500' : 'bg-blue-500'}`}></span>
                )}
              </div>
              <div className="text-xs text-gray-500 mt-2 text-right">
                Simulation T: {activeTask.time ? activeTask.time.toFixed(2) : '0.00'}s
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* CENTER: 3D Globe Viewer */}
      <div className="flex-1 relative">
        <GlobeSim activeTask={activeTask} />
      </div>

    </div>
  );
}

function MetricCard({ icon, label, value, color }) {
  return (
    <div className="p-4 bg-white/5 rounded-xl border border-white/5 flex items-center gap-4">
      <div className={`w-10 h-10 rounded-lg bg-white/5 flex items-center justify-center ${color}`}>
        {icon}
      </div>
      <div>
        <p className="text-xs text-gray-500 font-medium uppercase tracking-wider">{label}</p>
        <p className="text-xl font-bold font-mono tracking-tight">{value}</p>
      </div>
    </div>
  );
}

export default App;
