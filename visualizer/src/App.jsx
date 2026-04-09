import { useState, useEffect } from 'react';
import Papa from 'papaparse';
import { Activity, Clock, Zap, Cpu, Orbit, TerminalSquare, Play, Pause, SkipForward } from 'lucide-react';
import GlobeSim from './components/GlobeSim';

function App() {
  const [data, setData] = useState({ qml: [], qrl: [] });
  const [activeAlgo, setActiveAlgo] = useState('qml'); // 'qml' or 'qrl'
  const [timeIndex, setTimeIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(true);

  // Load CSV Data
  useEffect(() => {
    const loadCsv = async (file, key) => {
      const response = await fetch(`/${file}`);
      const text = await response.text();
      Papa.parse(text, {
        header: true,
        dynamicTyping: true,
        skipEmptyLines: true,
        complete: (results) => {
          setData(prev => ({ ...prev, [key]: results.data }));
        }
      });
    };
    loadCsv('qml.csv', 'qml');
    loadCsv('qrl.csv', 'qrl');
  }, []);

  const activeData = data[activeAlgo];
  const activeTask = activeData[timeIndex] || {};

  // Playback Loop
  useEffect(() => {
    let interval;
    if (isPlaying && activeData.length > 0) {
      interval = setInterval(() => {
        setTimeIndex(prev => (prev < activeData.length - 1 ? prev + 1 : 0));
      }, 50); // 50ms per step
    }
    return () => clearInterval(interval);
  }, [isPlaying, activeData]);

  // Aggregate Metrics over time (just read the CSV row)
  const currentLatency = activeTask.latency ? activeTask.latency.toFixed(3) : "0.000";
  const currentQ = activeTask.queue || 0;
  const currentEnergy = activeTask.energy ? Math.round(activeTask.energy) : 50000;
  const currentTput = activeTask.throughput_tasks ? activeTask.throughput_tasks.toFixed(1) : "0.0";

  return (
    <div className="w-full h-screen bg-[#050511] text-white flex overflow-hidden font-sans selection:bg-blue-500/30">
      
      {/* LEFT SIDEBAR: Metrics & Controls */}
      <div className="w-96 border-r border-white/10 bg-[#0a0a1a] flex flex-col relative z-10 shadow-2xl">
        <div className="p-6 border-b border-white/10">
          <div className="flex items-center gap-3 mb-2">
            <Orbit className="w-8 h-8 text-blue-500" />
            <h1 className="text-2xl font-bold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-emerald-400">
              SAGIN Command
            </h1>
          </div>
          <p className="text-gray-400 text-sm">Real-time Routing Simulation</p>
        </div>

        {/* Algorithm Toggle */}
        <div className="p-6 border-b border-white/10">
          <h2 className="text-xs uppercase tracking-wider text-gray-500 font-semibold mb-4">Controller Node</h2>
          <div className="flex bg-[#121226] p-1 rounded-lg">
            <button 
              onClick={() => setActiveAlgo('qml')}
              className={`flex-1 py-2 text-sm font-medium rounded-md transition-all ${activeAlgo === 'qml' ? 'bg-blue-600 text-white shadow' : 'text-gray-400 hover:text-white'}`}
            >
              QPPO (Proposed)
            </button>
            <button 
              onClick={() => setActiveAlgo('qrl')}
              className={`flex-1 py-2 text-sm font-medium rounded-md transition-all ${activeAlgo === 'qrl' ? 'bg-red-600/80 text-white shadow' : 'text-gray-400 hover:text-white'}`}
            >
              QEA2C (Baseline)
            </button>
          </div>
          <p className="text-xs text-gray-500 mt-3 h-8">
            {activeAlgo === 'qml' 
              ? "QPPO dynamically balances load across multiple LEO Slave Satellites."
              : "QEA2C relies heavily on the Master Satellite, risking bottlenecking."}
          </p>
        </div>

        {/* Live Metrics */}
        <div className="p-6 flex-1 overflow-y-auto">
          <h2 className="text-xs uppercase tracking-wider text-gray-500 font-semibold mb-4">Live Telemetry</h2>
          
          <div className="grid gap-4">
            <MetricCard icon={<Clock />} label="Current Latency" value={`${currentLatency} s`} color="text-yellow-400" />
            <MetricCard icon={<Activity />} label="Throughput" value={`${currentTput} t/s`} color="text-emerald-400" />
            <MetricCard icon={<TerminalSquare />} label="UAV Queue Depth" value={`${currentQ} pkts`} color="text-orange-400" />
            <MetricCard icon={<Zap />} label="Energy Reserve" value={`${currentEnergy} J`} color="text-cyan-400" />
            
            {/* Active Route Focus */}
            <div className="p-4 bg-white/5 rounded-xl border border-white/10 mt-4">
              <div className="flex items-center gap-2 mb-2">
                <Cpu className="w-4 h-4 text-gray-400" />
                <span className="text-sm font-medium text-gray-300">Active Route Target</span>
              </div>
              <div className="text-2xl font-bold flex items-center justify-between">
                <span>{activeTask.route === 1 ? 'Master Satellite' : activeTask.route === 0 ? 'Local Compute' : `Slave Satellite ${activeTask.route - 2}`}</span>
                <span className={`w-3 h-3 rounded-full animate-pulse ${activeTask.route === 1 ? 'bg-red-500' : 'bg-blue-500'}`}></span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* CENTER: 3D Globe Viewer */}
      <div className="flex-1 relative">
        <GlobeSim activeTask={activeTask} />
        
        {/* Timeline Overlay */}
        <div className="absolute bottom-8 left-1/2 -translate-x-1/2 w-3/4 max-w-2xl bg-[#0a0a1a]/80 backdrop-blur-md rounded-2xl border border-white/10 p-5 flex items-center gap-6 shadow-2xl">
          <button 
            onClick={() => setIsPlaying(!isPlaying)}
            className="w-12 h-12 bg-blue-600 hover:bg-blue-500 flex items-center justify-center rounded-full text-white transition-colors flex-shrink-0"
          >
            {isPlaying ? <Pause className="w-5 h-5" /> : <Play className="w-5 h-5 ml-1" />}
          </button>
          
          <div className="flex-1">
             <div className="flex justify-between text-xs text-gray-400 font-medium mb-2">
                <span>Time: {activeTask.time ? activeTask.time.toFixed(2) : 0}s</span>
                <span>Step {timeIndex} / {activeData.length}</span>
             </div>
             <input 
                type="range" 
                min="0" 
                max={Math.max(activeData.length - 1, 0)} 
                value={timeIndex} 
                onChange={(e) => {
                  setTimeIndex(parseInt(e.target.value));
                  setIsPlaying(false);
                }}
                className="w-full h-1 bg-white/20 rounded-lg appearance-none cursor-pointer accent-blue-500"
             />
          </div>
          
          <button 
             onClick={() => setTimeIndex(Math.max(activeData.length - 1, 0))}
             className="w-10 h-10 hover:bg-white/10 flex items-center justify-center rounded-full text-gray-400 transition-colors flex-shrink-0"
             title="Skip to End"
          >
             <SkipForward className="w-4 h-4" />
          </button>
        </div>
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
