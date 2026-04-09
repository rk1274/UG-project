import os

import random
import dag_generator
import orderDAG
import utils
import customexceptions
from pathlib import Path

import networkx as nx

class OrderManager:
    def __init__(self, num_init_orders: int, num_dynamic_orders: int, dynamic_deadline:int, size_to_shelves_map:dict,
                shelves_registry:dict, print_dags: bool, use_dags: bool):

        self._print_dags = print_dags

        self._init_orders = []
        self._dynamic_orders = []

        if use_dags:
            self.get_orders_from_folder(num_init_orders, num_dynamic_orders)
        else:
            self.generate_orders(num_init_orders, num_dynamic_orders, size_to_shelves_map, shelves_registry)

        self._dynamic_orders_intro_steps = {}
        self.generate_dynamic_order_introduction_times_uniform(dynamic_deadline)
    
    def generate_orders(self, num_init_orders: int, num_dynamic_orders: int, size_to_shelves_map, shelves_registry):
        if self._print_dags:
            self.clear_img_directory()

        order_id_ctr = 0
        for _ in range(num_init_orders):
            self.generate_order(self._init_orders, order_id_ctr, size_to_shelves_map, shelves_registry)

            order_id_ctr+=1

        for _ in range(num_dynamic_orders):
            self.generate_order(self._dynamic_orders, order_id_ctr, size_to_shelves_map, shelves_registry)

            order_id_ctr+=1

    def get_orders_from_folder(self, num_init_orders: int, num_dynamic_orders: int):
        if not os.path.exists(f"./{utils.DAG_FOLDER}/"):
            raise customexceptions.SimulationError("-d was provided but /%s does not exist" % utils.DAG_FOLDER)
        
        files = os.listdir(f"./{utils.DAG_FOLDER}/")

        orders = []

        order_id = 0
        for file in files:
            if Path(file).suffix.lower() != '.gml':
                continue

            dag = nx.read_gml(os.path.join(utils.DAG_FOLDER, file))
            ranks = dag_generator.compute_upward_ranks(dag)

            order = orderDAG.OrderDAG(dag, ranks, order_id)
            order_id+=1

            orders.append(order)

        total_needed = num_init_orders + num_dynamic_orders
        if len(orders) < total_needed:
            raise customexceptions.SimulationError(
                f"Need {total_needed} orders, but only found {len(orders)} .gml files."
            )

        self._init_orders = orders[:num_init_orders]
        self._dynamic_orders = orders[num_init_orders:total_needed]

        # print("using order", orders[0])
    
    def clear_img_directory(self):
        if not os.path.exists(f"./{utils.DAG_FOLDER}/"):
            os.makedirs(f"./{utils.DAG_FOLDER}/")

        for file in os.listdir(f"./{utils.DAG_FOLDER}/"):
            os.remove(os.path.join(f"./{utils.DAG_FOLDER}/", file))

    def generate_order(self, order_list, id, size_to_shelves_map, shelves_registry):
        l, m, s = random.randint(1, 3), random.randint(1, 4), random.randint(1, 5)

        goal_pos = [0, 3]
        dag_gen = dag_generator.DagGenerator(l, m, s, size_to_shelves_map, shelves_registry, goal_pos)
        dag_gen.generate_dag()
        if self._print_dags:
            # print(f"Saving DAG for order {id}...")
            dag_gen.save(f"order_{id}")

        order = orderDAG.OrderDAG(dag_gen.dag, dag_gen.ranks, id)
        order_list.append(order)

    def generate_dynamic_order_introduction_times_uniform(self, deadline):
        for ordr in self._dynamic_orders:
            selected_step = random.randint(1, deadline - 1)
            while selected_step in self._dynamic_orders_intro_steps.keys():
                selected_step = random.randint(1, deadline - 1)
            self._dynamic_orders_intro_steps[selected_step] = ordr

    def possibly_introduce_dynamic_order(self, step):
        if step in self._dynamic_orders_intro_steps.keys():
            return self._dynamic_orders_intro_steps[step]

    def get_init_orders(self):
        return self._init_orders








