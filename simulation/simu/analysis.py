import pandas as pd

def analyze_csv(file_path):
    try:
        df = pd.read_csv(file_path)
    except FileNotFoundError:
        print(f"Error: {file_path} not found.")
        return

    success_df = df[df['status'] == 'SUCCESS'].copy()
    
    success_df['total_steps'] = pd.to_numeric(success_df['total_steps'])
    success_df['avg_wait_pct'] = pd.to_numeric(success_df['avg_wait_pct'])

    stats = success_df.groupby('scheduler').agg({
        'total_steps': ['mean', 'std', 'min', 'max'],
        'avg_wait_pct': ['mean', 'std'],
        'seed': 'count'
    })

    stats.columns = [
        'Avg Steps', 'Std Dev Steps', 'Min Steps', 'Max Steps',
        'Avg Wait %', 'Std Dev Wait', 'Success Count'
    ]

    stats = stats.sort_values(by='Avg Steps')

    print("\n--- Scheduler Performance Summary ---")
    print(stats.round(2).to_string())
    
    best_scheduler = stats.index[0]
    print(f"\nInsight: '{best_scheduler}' is currently the most efficient (lowest avg steps).")

if __name__ == "__main__":
    analyze_csv("results/new_5_5x30.csv")