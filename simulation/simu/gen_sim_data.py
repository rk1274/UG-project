import warehouse
import random
import csv
import os
import customexceptions
import pandas as pd

def get_sim_data(warehouse_file, mode, seed_val, fault_rate=0.0025, use_battery=True, num_init_orders=5, num_dynamic_orders=5, max_steps=4000):
    """Runs a single simulation and returns the final stats."""

    random.seed(seed_val)

    simu = warehouse.Warehouse(
        num_init_orders, num_dynamic_orders,
        warehouse_file, mode, fault_rate, 
        use_battery, max_steps, False, True
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

    except customexceptions.FaultBlockingError as e:
        return {
            "scheduler": mode,
            "seed": seed_val,
            "total_steps": None,
            "avg_wait_pct": None,
            "status": "BLOCKED_BY_FAULT"+str(e),
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
    orders = [[5,5]]
    fault_rates = [0.0, 0.0025]
    fault_rates = [0.0]
    battery_options = [True, False]
    battery_options = [False]
    warehouse_files = ["whouses/whouse_2s_2o_6r.txt","whouses/whouse_2s_2o_5r.txt","whouses/whouse_2s_2o_4r.txt"]
    warehouse_files = ["whouses/whouse_2s_2o_4r.txt"]
    seeds = range(100, 200)

    # warehouse_file = "whouses/whouse_2s_2o_4r.txt"
    output_dir = "simple_dags/"

    robot_num = 5
    unique_id = 0
    for warehouse_file in warehouse_files:
        for order in orders:
            for fault_rate in fault_rates:
                for use_battery in battery_options:
                    all_results = []

                    for scheduler in schedulers:
                        print(f"Running {scheduler}...")
                        for s in seeds:
                            data = get_sim_data(warehouse_file, scheduler, s, fault_rate, use_battery,order[0], order[1])
                            all_results.append(data)

                    df = pd.DataFrame(all_results)
                    
                    df['rank'] = df.groupby('seed')['total_steps'].rank(method='min', ascending=True)
                    
                    output_path = f"{output_dir}{unique_id}_{robot_num}r_{fault_rate}_{use_battery}_{order[0]}_{order[1]}.csv"
                    # Save to CSV
                    df.to_csv(output_path, index=False)
                    print(f"\nSuccess! Data saved to {output_path}")

                    unique_id += 1
        robot_num -= 1