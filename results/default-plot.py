import matplotlib.pyplot as plt
import numpy as np

order = ['HEFT', 'DLS', 'HEFT-DLS', 'HEFT-DLS-DYN', 'SIMPLE']

avg_A = [1368.95, 1365.41, 1368.04, 1368.04, 1372.38]
min_A = [1161, 1122, 1125, 1125, 1126]
max_A = [1569, 1597, 1616, 1616, 1603]
std_A = [84.08, 85.58, 90.06, 90.06, 84.09]

avg_B = [1856.78, 1829.86, 1792.57, 1918.91, 1894.22]
min_B = [1324.0, 1311.0, 1409.0, 1316.0, 1352.0]
max_B = [3391.0, 2921.0, 2944.0, 3895.0, 3355.0]
std_B = [360.49, 326.74, 319.37, 522.50, 374.66]

x = np.arange(len(order))
width = 0.6

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 7), sharey=True)

def plot_scenario(ax, averages, mins, maxs, title, color):
    yerr = [np.array(averages) - np.array(mins), np.array(maxs) - np.array(averages)]
    ax.bar(x, averages, width, color=color, alpha=0.7, label='Mean Steps', edgecolor='black', zorder=3)
    ax.errorbar(x, averages, yerr=yerr, fmt='none', ecolor='#2c3e50', capsize=6, elinewidth=1.5, label='Min/Max', zorder=4)
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(order, rotation=20, ha='right')
    ax.grid(axis='y', linestyle='--', alpha=0.6, zorder=0)

plot_scenario(ax1, avg_A, min_A, max_A, 'Scenario A: Ideal Conditions', '#3498db')
plot_scenario(ax2, avg_B, min_B, max_B, 'Scenario B: Stress Conditions', '#e74c3c')

ax1.set_ylim(800, 4500) 
ax1.set_ylabel('Total Simulation Steps', fontsize=12, fontweight='bold')
ax1.legend()

plt.tight_layout()
plt.savefig('default-box-plot.png')