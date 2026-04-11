import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

data = {
    'Goals': [1, 2, 3, 4, 5, 6],
    'HEFT': [3423.29, 2851.46, 2764.31, 2656.69, 2633.10, 3041.73],
    'DLS': [3043.11, 2915.19, 2806.70, 2726.14, 2728.03, 2945.42],
    'HEFT-DLS': [3299.14, 3043.05, 2644.62, 2697.10, 2699.15, 2966.35],
    'Simple': [3191.03, 2926.61, 2651.17, 2697.38, 2776.64, 3024.78],
    'HEFT-DLS-Dyn': [3482.64, 3035.41, 2950.71, 2807.95, 2733.41, 2990.41]
}

df = pd.DataFrame(data)
df_melted = df.melt(id_vars='Goals', var_name='Scheduler', value_name='Avg_Steps')

plt.figure(figsize=(10, 6))
sns.set_style("whitegrid")
sns.lineplot(data=df_melted, x='Goals', y='Avg_Steps', hue='Scheduler', marker='s', linewidth=2)

plt.title('Scheduler Performance vs. Number of Goals', fontsize=14)
plt.xlabel('Number of Goals', fontsize=12)
plt.ylabel('Average Steps to Completion', fontsize=12)
plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')

plt.tight_layout()
plt.savefig('goal-plot.png')