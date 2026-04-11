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

schedulers = ['HEFT', 'DLS', 'HEFT-DLS', 'Simple', 'HEFT-DLS-Dyn']

data = {
    'Small':      [551.48, 552.25, 547.85, 550.71, 543.07],
    'Simple':     [1728.72, 1792.12, 1726.06, 1818.38, 1762.47],
    'Linear':     [1999.34, 1933.03, 1942.65, 2009.32, 1897.28],
    'Complex':    [2598.41, 2684.41, 2612.65, 2726.86, 2642.80]
}

ylimits = {
    'Small':      (500, 600),
    'Simple':     (1600, 1900),
    'Linear':     (1800, 2100),
    'Complex':    (2400, 2900)
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
    ax.set_xticklabels(schedulers, fontsize=11, color=COLOR_TEXT)
    ax.set_ylim(ylimits[category])
    
    for spine in ax.spines.values():
        spine.set_visible(False)
    
    ax.grid(axis='y', linestyle='--', linewidth=0.7, color=COLOR_GRID, alpha=0.5)
    ax.set_axisbelow(True)
    
    ax.bar_label(bars, fmt='%.1f', padding=5, fontsize=11, weight='bold', color=COLOR_TEXT)

plt.tight_layout(pad=4.0)

plt.savefig('dag_complexity.png', dpi=300, bbox_inches='tight')