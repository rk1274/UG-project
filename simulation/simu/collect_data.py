import warehouse
import random
import csv
import os
import customexceptions

def get_sim_data(warehouse_file, mode, seed_val):
    """Runs a single simulation and returns the final stats."""

    random.seed(seed_val)
    fault_rate = 0.0025 # default 0.0025, set to 0.0 for no faults.
    use_battery = True

    num_init_orders = 5
    num_dynamic_orders = 5

    max_steps = 4000

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

    schedulers = ["simple", "heft", "dls", "heft-dls"]
    seeds = range(100, 200)
    warehouse_file = "whouse.txt"
    output_file = "results/5_5_0.0025x100.csv"

    all_results = []

    for scheduler in schedulers:
        for s in seeds:
            data = get_sim_data(warehouse_file, scheduler, s)
            all_results.append(data)
        print("Done.")

    keys = all_results[0].keys()
    with open(output_file, 'w', newline='') as f:
        dict_writer = csv.DictWriter(f, fieldnames=keys)
        dict_writer.writeheader()
        dict_writer.writerows(all_results)

    print(f"\nSuccess! Data saved to {output_file}")