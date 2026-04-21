import warehouse
import random
import csv
import os
import customexceptions
import pandas as pd

def get_sim_data(warehouse_file, mode, seed_val, fault_rate=0.0025, use_battery=True, num_init_orders=5, num_dynamic_orders=5, max_steps=7000):
    """Runs a single simulation and returns the final stats."""

    random.seed(seed_val)

    simu = warehouse.Warehouse(
        num_init_orders, num_dynamic_orders,
        warehouse_file, mode, fault_rate, 
        use_battery, max_steps, False, False
    )

    try:
        while not simu.step():
            pass
    
        total_steps = simu.get_total_steps()
        num_robots = len(simu._robots)
        overall_wait = 0
        for robot in simu._robots.values():
            overall_wait += sum(1 for status in robot.status_history if status == "W")

        avg_wait_pct = (overall_wait / (total_steps * num_robots)) * 100
        
        return {
            "scheduler": mode,
            "seed": seed_val,
            "total_steps": total_steps,
            "avg_wait_pct": round(avg_wait_pct, 2),
            "status": "SUCCESS"
        }
    
    except customexceptions.SimulationError as e:
        return {
            "scheduler": mode,
            "seed": seed_val,
            "total_steps": None, 
            "avg_wait_pct": None,
            "status": "SIM_ERROR"+str(e),
        }

if __name__ == "__main__":
    os.environ["ROBOTSIM_TRANSMIT"] = "False"
    schedulers = ["simple", "heft", "dls", "heft-dls", "heft-dls-dyn"]

    # Scalability test:
    orders = [[1,0],[5,0],[5,5],[10,0],[10,10],[20,10],[30,20],[50,50]]

    # Default:
    orders = [[10,10]]

    # Default test:
    # fault_rates = [0.0025, 0.0]

    # Default:
    fault_rates = [0.0025]
    
    # Default test:
    # battery_options = [True, False]
    
    # Default:
    battery_options = [True]

    # Different numbers of robots:
    # warehouse_files = ["whouses/whouse_2s_2o_6r.txt","whouses/whouse_2s_2o_5r.txt","whouses/whouse_2s_2o_4r.txt","whouses/whouse_2s_2o_3r.txt","whouses/whouse_2s_2o_2r.txt"]

    # Different numbers of shelves:
    # warehouse_files = ["whouses/whouse_1s_2o_4r.txt","whouses/whouse_2s_2o_4r.txt","whouses/whouse_3s_2o_4r.txt","whouses/whouse_4s_2o_4r.txt"]
    
    # Different numbers of goals:
    # warehouse_files = ["whouses/whouse_2s_1o_4r.txt","whouses/whouse_2s_2o_4r.txt","whouses/whouse_2s_3o_4r.txt","whouses/whouse_2s_4o_4r.txt","whouses/whouse_2s_5o_4r.txt","whouses/whouse_2s_6o_4r.txt"]
    
    # Default layout:
    warehouse_files = ["whouses/whouse_2s_2o_4r.txt"]

    seeds = range(100, 200)

    output_dir = "results/"

    unique_id = 0
    for warehouse_file in warehouse_files:
        for order in orders:
            for fault_rate in fault_rates:
                for battery_option in battery_options:

                    all_results = []
                    for scheduler in schedulers:
                        print(f"Running {scheduler}...")
                        for s in seeds:
                            data = get_sim_data(warehouse_file, scheduler, s, fault_rate, battery_option,order[0], order[1])
                            all_results.append(data)

                    df = pd.DataFrame(all_results)
                    
                    df['rank'] = df.groupby('seed')['total_steps'].rank(method='min', ascending=True)
                    
                    output_path = f"{output_dir}{unique_id}.csv"

                    df.to_csv(output_path, index=False)
                    print(f"\nSuccess! Data saved to {output_path}")

                    unique_id += 1