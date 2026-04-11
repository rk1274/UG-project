import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

data = {
    'Shelves': [1, 2, 3, 4],
    'HEFT': [2605.86, 2633.10, 2823.45, 3197.23],
    'DLS': [2630.97, 2728.03, 3052.04, 3328.14],
    'HEFT-DLS': [2497.14, 2699.15, 2981.85, 3076.36],
    'Simple': [2614.86, 2776.64, 2970.47, 3285.07],
    'HEFT-DLS-Dyn': [2669.92, 2733.41, 2997.64, 3484.89]
}

df = pd.DataFrame(data)
df_melted = df.melt(id_vars='Shelves', var_name='Scheduler', value_name='Avg_Steps')

plt.figure(figsize=(10, 6))
sns.set_style("whitegrid")
sns.lineplot(data=df_melted, x='Shelves', y='Avg_Steps', hue='Scheduler', 
             marker='o', linewidth=2, markersize=8)

plt.title('Scheduler Performance vs. Number of Shelves', fontsize=14)
plt.xlabel('Number of Shelves', fontsize=12)
plt.ylabel('Average Steps to Completion', fontsize=12)
plt.xticks([1, 2, 3, 4])
plt.legend(title='Scheduler', bbox_to_anchor=(1.05, 1), loc='upper left')

plt.tight_layout()
plt.savefig('shelf-plot.png', dpi=300)