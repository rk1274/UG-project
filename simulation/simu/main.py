import warehouse
import os
import argparse
import time
import utils
import random

def run_simple_sim(warehouse_file, transmit=False, print_dags=False, mode="simple", use_dags=False):
    """
    A simplified runner that just starts the simulation and 
    loops until all tasks are complete.
    """
    os.environ["ROBOTSIM_TRANSMIT"] = str(transmit)

    # TODO inv should always be 1.
    inv_size = 1         

    # TODO faults ofc.
    fault_rate = 0.005
    
    step_limit = 2000     
    
    print(f"Initializing Warehouse: {warehouse_file}...")
    
    simu = warehouse.Warehouse(
        warehouse_file, 
        inv_size, 
        mode, 
        fault_rate, 
        step_limit,
        print_dags,
        use_dags
    )

    print("Starting Simulation Loop...")
    
    keep_running = True
    while keep_running:
        if transmit:
            time.sleep(0.2)
            
        finished = simu.step()
        keep_running = not finished
        
        if simu.get_total_steps() % 50 == 0:
            print(f"Step: {simu.get_total_steps()}...")

    for robot in simu._robots.values():
        print(f"{robot.get_name()} had {robot.num_faults} faults.")

    print(f"Simulation Complete in {simu.get_total_steps()} steps.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", action="store_true", help="Transmit UDP packets for visualization")
    parser.add_argument("-p", action="store_true", help="Print visualisations of the generated DAGs")
    parser.add_argument("-s", type=str, default="simple", help="The scheduler to use. 'simple', 'heft' or 'heft-dls'")
    parser.add_argument("-d", action="store_true", help=f"Use /{utils.DAG_FOLDER} as the dags for the simulation")
    parser.add_argument("-f", type=str, default="whouse.txt", help="The warehouse layout file")
    parser.add_argument("-r", type=int, help="The random seed to use")
    args = parser.parse_args()
    
    if args.r:
        random.seed(args.r)

    run_simple_sim(args.f, transmit=args.t, print_dags=args.p, mode=args.s, use_dags=args.d)