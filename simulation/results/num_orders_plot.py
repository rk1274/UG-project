import pandas as pd
import matplotlib.pyplot as plt
import glob
import os

path = 'different_orders/'
all_files = glob.glob(os.path.join(path, "*_True_*.csv"))

if not all_files:
    print("No CSV files found. Check your path and naming convention.")
    exit()

li = []
for filename in all_files:
    base = os.path.basename(filename).replace('.csv', '')
    parts = base.split('_')
    
    try:
        init_o, dyn_o = int(parts[2]), int(parts[3])
        total_o = init_o + dyn_o
        
        df = pd.read_csv(filename)
        df['total_orders'] = total_o
        df['config_label'] = f"{init_o}+{dyn_o}"
        li.append(df)
    except (IndexError, ValueError):
        print(f"Skipping {filename}: unexpected format.")

full_df = pd.concat(li, axis=0, ignore_index=True)
success_df = full_df[full_df['status'] == 'SUCCESS'].copy()
success_df['steps_per_order'] = success_df['total_steps'] / success_df['total_orders']

summary = success_df.groupby(['config_label', 'scheduler'])['total_steps'].mean().unstack()

order_sequence = ['1+0', '5+0', '5+5', '10+0', '10+10', '20+10', '30+20', '50+50']
available_labels = [label for label in order_sequence if label in summary.index]
summary = summary.reindex(available_labels)

delta_summary_pct = summary.subtract(summary['simple'], axis=0).div(summary['simple'], axis=0) * 100

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 12))

efficiency_summary = success_df.groupby(['config_label', 'scheduler'])['steps_per_order'].mean().unstack()
efficiency_summary = efficiency_summary.reindex(available_labels)
efficiency_summary.plot(marker='o', ax=ax1, linewidth=2)
ax1.set_title('Scheduler Efficiency (Steps per Order)', fontsize=14, fontweight='bold')
ax1.set_ylabel('Avg Steps / Order')
ax1.grid(True, linestyle='--', alpha=0.6)
ax1.legend(title="Scheduler", bbox_to_anchor=(1.05, 1), loc='upper left')

delta_summary_pct.plot(marker='s', ax=ax2, linewidth=2)
ax2.axhline(0, color='black', linestyle='-', linewidth=1.5) # Baseline
ax2.set_title('Performance % Difference vs. Simple Baseline', fontsize=14, fontweight='bold')
ax2.set_ylabel('% Faster (-) or Slower (+) than Simple')
ax2.set_xlabel('Order Configuration (Initial + Dynamic)')
ax2.grid(True, linestyle='--', alpha=0.6)

import matplotlib.ticker as mtick
ax2.yaxis.set_major_formatter(mtick.PercentFormatter())

plt.tight_layout()
plt.savefig('scale-plot.png', bbox_inches='tight')