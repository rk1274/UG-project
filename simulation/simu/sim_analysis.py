import pandas as pd
from natsort import natsorted
from pathlib import Path

def analyze_csv(file_path, yeah):
    try:
        df = pd.read_csv(file_path)
    except FileNotFoundError:
        print(f"Error: {file_path} not found.")
        return

    success_df = df[df['status'] == 'SUCCESS'].copy()
    
    success_df['total_steps'] = pd.to_numeric(success_df['total_steps'])
    success_df['rank'] = pd.to_numeric(success_df['rank'])

    success_df['is_first'] = (success_df['rank'] == 1)

    stats = success_df.groupby('scheduler').agg({
        'total_steps': ['mean', 'std', 'min', 'max'],
        'rank': 'mean',
        'is_first': 'sum',
        'seed': 'count'
    })

    stats.columns = [
        'Avg Steps', 'Std Dev Steps', 'Min Steps', 'Max Steps',
        'Avg Rank', '1st Place Wins', 'Success Count'
    ]

    stats = stats.sort_values(by='Avg Steps')

    if yeah:
        id, fault_rate, use_battery, num_init_orders, num_dynamic_orders = file_path.name.split('_')

        print(f"\n--- Analysis for: ---")
        print(f"\nFault Rate: {fault_rate}\nUse Battery: {use_battery}, ")
        print(f"Initial Orders: {num_init_orders}\nDynamic Orders: {num_dynamic_orders}")

    else:
        s_def, o_def, r_def = "", "", ""

        id, shelves, order_stations, robots = file_path.name.split('_')
        if int(robots[0]) == 4:
            r_def = " (default)"
        if int(shelves[0]) == 2:
            s_def = " (default)"
        if int(order_stations[0]) == 2:
            o_def = " (default)"

        print(f"\n--- Analysis for: ---")
        print(f"\nNo faults. 5x5 orders.")
        print(f"\nShelves: {shelves[0]}{s_def}\nOrder stations: {order_stations[0]}{o_def}\nRobots: {robots[0]}{r_def} ")

    print("\n--- Scheduler Performance Summary ---")
    print(stats.round(2).to_string())
    
    best_by_steps = stats.sort_values(by='Avg Steps').index[0]
    best_by_rank = stats.index[0]
    
    print(f"\nInsight: '{best_by_steps}' has the lowest average steps.")
    print(f"Insight: '{best_by_rank}' is the most consistent winner (best avg rank).")

if __name__ == "__main__":
    # directory = Path('different_layout_results/no_faults_10x5')
    directory = Path('different_layout_results/no_faults_order_stations')
    # directory = Path('5_robot_layout_results')


    files = natsorted(directory.rglob('*'))

    for file_path in files:
        if file_path.is_file():
            # print(f"\nAnalyzing {file_path.name}...")
            analyze_csv(file_path, yeah=False)