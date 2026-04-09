import pandas as pd
import glob
for f in glob.glob('results/*.csv'):
    try:
        df = pd.read_csv(f)
        print(f)
        if 'deadline_met' in df: print("  Deadlines success:", df['deadline_met'].mean())
        if 'route' in df: print("  Route mean:", df['route'].mean())
        if 'latency' in df: print("  Latency mean:", df['latency'].mean())
    except Exception as e:
        print(f, "failed", e)
