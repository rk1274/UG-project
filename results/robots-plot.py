import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

data = {
    'Robots': [2, 3, 4, 5, 6],
    'Simple': [4532.00, 3379.80, 2776.64, 2317.93, 1949.75],
    'DLS': [4538.12, 3449.05, 2728.03, 2270.12, 1888.32],
    'HEFT': [4638.84, 3318.21, 2633.10, 2343.96, 1894.46],
    'HEFT-DLS': [4746.63, 3270.17, 2699.15, 2179.63, 1853.30],
    'HEFT-DLS-Dyn': [5319.65, 3524.08, 2733.41, 2340.48, 1934.79]
}

df = pd.DataFrame(data).set_index('Robots')

df_plot = df.T

plt.figure(figsize=(12, 7))

sns.heatmap(
    df_plot, 
    annot=True, 
    fmt=".1f", 
    cmap="RdYlGn_r", 
    cbar_kws={'label': 'Average Steps'},
    linewidths=.5
)

plt.title('Scheduler Performance Heatmap: Average Steps', fontsize=14)
plt.xlabel('Number of Robots', fontsize=12)
plt.ylabel('Scheduling Algorithm', fontsize=12)

plt.tight_layout()
plt.savefig('robot-plot.png', dpi=300)