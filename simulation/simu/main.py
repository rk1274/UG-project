import warehouse
import os
import argparse
import time

def run_simple_sim(warehouse_file, transmit=False):
    """
    A simplified runner that just starts the simulation and 
    loops until all tasks are complete.
    """
    # 1. Setup Environment
    os.environ["ROBOTSIM_TRANSMIT"] = str(transmit)

    inv_size = 1          # Robot carrying capacity
    schedule_mode = "simple" 
    fault_rates = [0, 0, 0, 0] # [Battery, Motor, Sensor, Comms]
    fault_mode = True      # Enable/Disable fault tolerance logic
    step_limit = 2000      # Safety cutoff
    
    print(f"Initializing Warehouse: {warehouse_file}...")
    
    # 3. Initialize the Warehouse
    # This triggers the OrderManager and Scheduler internally
    simu = warehouse.Warehouse(
        warehouse_file, 
        inv_size, 
        schedule_mode, 
        fault_rates, 
        fault_mode, 
        step_limit
    )

    print("Starting Simulation Loop...")
    
    # 4. Main Simulation Loop
    keep_running = True
    while keep_running:
        # If transmitting to visualizer, slow down so you can actually see it
        if transmit:
            time.sleep(0.5)
            
        # simu.step() returns True when all orders are finished or an error occurs
        finished = simu.step()
        keep_running = not finished
        
        if simu.get_total_steps() % 50 == 0:
            print(f"Step: {simu.get_total_steps()}...")

    print(f"Simulation Complete in {simu.get_total_steps()} steps.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", action="store_true", help="Transmit UDP packets for visualization")
    parser.add_argument("-f", type=str, default="whouse.txt", help="The warehouse layout file")
    args = parser.parse_args()

    run_simple_sim(args.f, transmit=args.t)