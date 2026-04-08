import matplotlib.pyplot as plt
import numpy as np

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.size": 12
})

COLOR_PRIMARY = '#4C78A8' 
COLOR_WINNER = '#54A24B' 
COLOR_TEXT = '#2b2b2b'
COLOR_GRID = '#cccccc'

# --- DATA ---
schedulers = ['HEFT-DLS', 'HEFT', 'DLS', 'Simple']

data = {
    'Small':      [313.35, 336.10, 322.45, 326.79],
    'Simple':     [648.69, 647.00, 659.82, 657.31],
    'Linear':     [655.48, 644.69, 662.54, 655.63],
    'Complex':    [1081.86, 1093.47, 1115.64, 1130.38]
}

ylimits = {
    'Small':      (280, 360),
    'Simple':     (600, 700),
    'Linear':     (600, 700),
    'Complex':    (1000, 1200)
}

x = np.arange(len(schedulers))
width = 0.6

fig, axes = plt.subplots(2, 2, figsize=(14, 10))
axes = axes.flatten()
titles = list(data.keys())

for i, ax in enumerate(axes):
    category = titles[i]
    vals = data[category]
    
    min_idx = np.argmin(vals)
    colors = [COLOR_WINNER if j == min_idx else COLOR_PRIMARY for j in range(len(schedulers))]
    
    bars = ax.bar(x, vals, width, color=colors, edgecolor='none', alpha=0.85)
    
    ax.set_title(f'{category} DAGs', fontsize=16, weight='bold', color=COLOR_TEXT, pad=15)
    if i % 2 == 0:
        ax.set_ylabel('Average Steps', fontsize=14, color=COLOR_TEXT)
    
    ax.set_xticks(x)
    ax.set_xticklabels(schedulers, fontsize=12, color=COLOR_TEXT)
    ax.set_ylim(ylimits[category])
    
    for spine in ax.spines.values():
        spine.set_visible(False)
    
    ax.grid(axis='y', linestyle='--', linewidth=0.7, color=COLOR_GRID, alpha=0.5)
    ax.set_axisbelow(True)
    
    ax.bar_label(bars, fmt='%.1f', padding=5, fontsize=11, weight='bold', color=COLOR_TEXT)

plt.tight_layout(pad=4.0)

plt.savefig('dag_topology_comparison.png', dpi=300, bbox_inches='tight')
print("Saved: dag_topology_comparison.png")