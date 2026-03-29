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

    fault_rate = 0.005 # Set to 0.0 for no faults. otherwise 0.005
    use_battery = True # Set to False for no battery.
    
    step_limit = 2000     
    
    num_init_orders = 5
    num_dynamic_orders = 5

    print(f"Initializing Warehouse: {warehouse_file}...")
    
    simu = warehouse.Warehouse(
        num_init_orders,
        num_dynamic_orders,
        warehouse_file, 
        mode, 
        fault_rate, 
        use_battery,
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

    overall_time_waiting = 0
    overall_time_active = 0

    for robot in simu._robots.values():
        print(f"{robot.get_name()} had {robot.num_faults} faults.")

        if len(robot.status_history) != simu.get_total_steps():
            print("wtf, hist: %d, steps: %d", len(robot.status_history), simu.get_total_steps())

        time_waiting = 0
        time_active = 0
        for status in robot.status_history:
            if status == "W":
                time_waiting += 1

            if status == "A":
                time_active += 1

        overall_time_waiting += time_waiting
        overall_time_active += time_active

        print("Time spent waiting: %.1f%%" % ((time_waiting/simu.get_total_steps())*100))
        print("Time spent active: %.1f%%" % ((time_active/simu.get_total_steps())*100))

    
    print("\nOverall time spent waiting: %.1f%%" % ((overall_time_waiting/(simu.get_total_steps()*len(simu._robots)))*100))
    print("Overall time spent active: %.1f%%" % ((overall_time_active/(simu.get_total_steps()*len(simu._robots)))*100))
    

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