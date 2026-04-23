from email.policy import default

import pandas as pd
from natsort import natsorted
from pathlib import Path

filter = False

def analyze_csv(file_path, mode):
    try:
        df = pd.read_csv(file_path)
    except FileNotFoundError:
        print(f"Error: {file_path} not found.")
        return

    num_schedulers = df['scheduler'].nunique()
    
    def all_successful(group):
        if filter:
            return (group['status'] == 'SUCCESS').all() and len(group) == num_schedulers
       
        return True

    valid_seeds = df.groupby('seed').filter(all_successful)['seed'].unique()
    
    filtered_df = df[df['seed'].isin(valid_seeds)].copy()
    
    total_seeds = df['seed'].nunique()
    dropped_count = total_seeds - len(valid_seeds)


    success_df = filtered_df.copy() 
    
    success_df['total_steps'] = pd.to_numeric(success_df['total_steps'])
    success_df['rank'] = success_df.groupby('seed')['total_steps'].rank(method='min')
    success_df['is_first'] = (success_df['rank'] == 1)
    success_df['is_success'] = (success_df['status'] == 'SUCCESS')

    stats = success_df.groupby('scheduler').agg({
        'total_steps': ['mean', 'std', 'min', 'max'],
        'rank': 'mean',
        'is_first': 'sum',
        'is_success': 'sum',
    })

    stats.columns = [
        'Avg Steps', 'Std Dev Steps', 'Min Steps', 'Max Steps',
        'Avg Rank', '1st Place Wins', 'Success Count'
    ]

    stats = stats.sort_values(by='Avg Steps')
    print(f"Total seeds processed: {total_seeds}")
    print(f"Seeds excluded (failed in at least one method): {dropped_count}")

    if mode == "initial":
        id, faults, num_init_orders, num_dynamic_orders = file_path.name.split('_')

        if faults == "False":
            return

        print(f"\n--- Analysis for: ---")
        print(f"\nFault enabled?: {faults}")
        print(f"Initial Orders: {num_init_orders}\nDynamic Orders: {num_dynamic_orders}")
    elif mode == "default":
        id,use_battery,  fault_rate  = file_path.name.split('_')
        print(f"\n--- Analysis for: ---")
        print(f"\nFault Rate: {fault_rate}\nUse Battery: {use_battery}, ")

    elif mode == "complex_dags":
        type = file_path.name.split('_')[0]
        print(f"\n--- Analysis for {type} dags: ---")

    elif mode == "robots":
        num = file_path.name.split('_')[0]
        print(f"\n--- Analysis for {num} robots: ---")

    elif mode == "shelves":
        num = file_path.name.split('_')[0]
        print(f"\n--- Analysis for {num} shelves: ---")

    elif mode == "goals":
        num = file_path.name.split('_')[0]
        print(f"\n--- Analysis for {num} goals: ---")

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
    # directory = Path('different_orders')
    # mode = "initial"

    # directory = Path('sim_results')
    # mode = "robots"

    # directory = Path('shelf_results')
    # mode = "shelves"

    directory = Path('goal_results')
    mode = "goals"

    directory = Path('DAG-complexity')
    mode = "complex_dags"

    # directory = Path('complex_dags')
    # mode = "complex_dags"

    # directory = Path('5_robot_layout_results')
    # mode = "layout_comparison"

    # directory = Path('default')
    # mode = "default"

    files = natsorted(directory.rglob('*'))

    for file_path in files:
        if file_path.is_file():
            analyze_csv(file_path, mode)