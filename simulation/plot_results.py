import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# Set aesthetic styling
sns.set_theme(style="whitegrid", context="paper", font_scale=1.2)
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Roboto', 'Arial', 'Inter']

RESULTS_DIR = "results"
OUTPUT_DIR = "plots"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Define controllers and their pretty names + colors
CONTROLLERS = {
    "random": ("Random", "#9E9E9E"),
    "smart": ("Greedy Heuristic", "#F44336"),
    "rl": ("Tabular Q-Learning", "#FF9800"),
    "drl": ("Classical PPO (DRL)", "#2196F3"),
    "qrl": ("Paper Baseline (QEA2C)", "#9C27B0"),
    "qml_routing": ("Proposed (QPPO)", "#4CAF50")
}

def load_data():
    dfs = {}
    for ctrl_id, (name, color) in CONTROLLERS.items():
        path = os.path.join(RESULTS_DIR, f"results_controller_{ctrl_id}.csv")
        if os.path.exists(path):
            df = pd.read_csv(path)
            # Ensure proper numeric typing
            df['latency'] = pd.to_numeric(df['latency'], errors='coerce')
            df['time'] = pd.to_numeric(df['time'], errors='coerce')
            dfs[ctrl_id] = df
    return dfs

def plot_latency_comparison(dfs):
    plt.figure(figsize=(10, 6))
    
    for ctrl_id, df in dfs.items():
        name, color = CONTROLLERS[ctrl_id]
        # Smooth the latency with a rolling window for clearer visualization
        df_smoothed = df.sort_values('time')
        # Only plot where latency is not null
        df_valid = df_smoothed.dropna(subset=['latency'])
        
        if len(df_valid) == 0:
            continue
            
        smoothed_latency = df_valid['latency'].rolling(window=5, min_periods=1).mean()
        
        plt.plot(df_valid['time'], smoothed_latency, 
                 label=name, color=color, linewidth=2.5, alpha=0.9)
                 
    plt.title('Average Task Latency over Time', fontsize=16, fontweight='bold', pad=15)
    plt.xlabel('Simulation Time (s)', fontsize=14)
    plt.ylabel('Latency (s)', fontsize=14)
    plt.legend(frameon=True, shadow=True, fancybox=True, loc='upper left')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "latency_comparison.png"), dpi=300, bbox_inches='tight')
    plt.close()

def plot_uav_congestion(dfs):
    compare_set = ["smart", "qrl", "qml_routing"]
    
    plt.figure(figsize=(10, 6))
    
    for ctrl_id in compare_set:
        if ctrl_id not in dfs: continue
        df = dfs[ctrl_id]
        name, color = CONTROLLERS[ctrl_id]
        
        # Plot UAV Load (load0)
        plt.plot(df['time'], df['load0'], 
                 label=f"{name} (UAV Load)", color=color, linewidth=2.5)
                 
    # Add UAV capacity line
    plt.axhline(y=4, color='r', linestyle='--', alpha=0.8, linewidth=2, label='UAV Capacity (Bottleneck)')
    
    plt.title('UAV Congestion Management: Greedy vs Quantum', fontsize=16, fontweight='bold', pad=15)
    plt.xlabel('Simulation Time (s)', fontsize=14)
    plt.ylabel('Concurrent Tasks on UAV', fontsize=14)
    plt.legend(frameon=True, shadow=True)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.fill_between([0, 50], 4, 20, color='red', alpha=0.05) # highlight danger zone
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "uav_congestion.png"), dpi=300, bbox_inches='tight')
    plt.close()

def plot_routing_distribution(dfs):
    # Plot how QML distributed its traffic
    if 'qml_routing' not in dfs: return
    df = dfs['qml_routing']
    
    route_counts = df['route'].value_counts().sort_index()
    
    labels = []
    for r in route_counts.index:
        if r == 0: labels.append("UAV (Local)")
        elif r == 1: labels.append("Master Satellite")
        else: labels.append(f"Slave Sat {int(r)}")
        
    plt.figure(figsize=(9, 9))
    colors = sns.color_palette("viridis", len(route_counts))
    
    explode = [0.05] * len(route_counts)
    if 1 in route_counts.index: # highlight master sat if present
        idx = list(route_counts.index).index(1)
        explode[idx] = 0.15
        
    plt.pie(route_counts, labels=labels, autopct='%1.1f%%', startangle=140, 
            colors=colors, explode=explode, shadow=True, 
            textprops={'fontsize': 12, 'fontweight': 'bold'})
            
    plt.title('Quantum PPO: Intelligent Load Distribution', fontsize=16, fontweight='bold', pad=20)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "qml_route_distribution.png"), dpi=300, bbox_inches='tight')
    plt.close()

def plot_deadline_success(dfs):
    names = []
    rates = []
    colors = []
    
    for ctrl_id, df in dfs.items():
        name, color = CONTROLLERS[ctrl_id]
        if 'deadline_met' in df.columns:
            # Drop NaN from deadline_met in case of partial rows
            valid = df['deadline_met'].dropna()
            if len(valid) > 0:
                success_rate = (valid.sum() / len(valid)) * 100
                names.append(name)
                rates.append(success_rate)
                colors.append(color)
            
    plt.figure(figsize=(10, 6))
    bars = plt.bar(names, rates, color=colors, edgecolor='black', linewidth=1)
    
    # Add percentages on top of bars
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height - 5,
                 f'{height:.1f}%', ha='center', va='bottom', 
                 fontsize=13, fontweight='bold', color='white')
                 
    plt.title('Deadline Satisfaction Rate (< Task Deadline)', fontsize=16, fontweight='bold', pad=15)
    plt.ylabel('Success Rate (%)', fontsize=14)
    plt.ylim(0, 105)
    plt.xticks(rotation=15, ha='right', fontsize=12)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "deadline_success.png"), dpi=300, bbox_inches='tight')
    plt.close()

if __name__ == "__main__":
    print("Loading simulation results...")
    dfs = load_data()
    print(f"Loaded {len(dfs)} result files.")
    
    print("Generating visualizations...")
    plot_latency_comparison(dfs)
    plot_uav_congestion(dfs)
    plot_routing_distribution(dfs)
    plot_deadline_success(dfs)
    print(f"Saved visualizations to {OUTPUT_DIR}/")
