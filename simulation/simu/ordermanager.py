import os

import random
import dag_generator
import orderDAG
import time

class OrderManager:
    def __init__(self, num_init_orders: int, num_dynamic_orders: int, dynamic_deadline:int, size_to_shelves:dict, shelves_registry:dict):
        self._num_init_orders = num_init_orders
        self._num_dynamic_orders = num_dynamic_orders
        self._dynamic_deadline = dynamic_deadline

        self._init_orders = []
        self._dynamic_orders = []

        self._order_intro_times = {}
        self._order_work_start_times = {}
        self._order_completion_times = {}
        self._all_orders = {}
        self.generate_orders(num_init_orders, num_dynamic_orders, size_to_shelves, shelves_registry)

        for ordr in self._init_orders:
            self._order_intro_times[ordr.get_id()] = 0

        self._dynamic_orders_intro_steps = {}
        self.generate_dynamic_order_introduction_times_uniform(self._dynamic_deadline)

    def get_dynamic_deadline(self):
        return self._dynamic_deadline
    
    def set_order_start_work_time(self, order_id, step_value):
        self._order_work_start_times[order_id] = step_value

    def set_order_completion_time(self, ordr: orderDAG.OrderDAG, step_value:int):
        self._order_completion_times[ordr.get_id()] = step_value

    def generate_orders(self, num_init_orders: int, num_dynamic_orders: int, size_to_shelves, shelves_registry):
        self.clear_img_directory()

        order_id_ctr = 0
        for _ in range(num_init_orders):
            self.generate_order(self._init_orders, order_id_ctr, size_to_shelves, shelves_registry)

            order_id_ctr+=1

        for _ in range(num_dynamic_orders):
            self.generate_order(self._dynamic_orders, order_id_ctr, size_to_shelves, shelves_registry)

            order_id_ctr+=1
    
    def clear_img_directory(self):
        if not os.path.exists("./data/"):
            os.makedirs("./data/")

        for file in os.listdir("./data/"):
            os.remove(os.path.join("./data/", file))

    def generate_order(self, order_list, id, size_to_shelves, shelves_registry):
        l, m, s = random.randint(1, 3), random.randint(1, 4), random.randint(1, 5)
            
        goal_pos = [0, 3]
        dag_gen = dag_generator.Order(l, m, s, size_to_shelves, shelves_registry, goal_pos)
        dag_gen.generate_dag()
        dag_gen.save_image(f"order_{id}")

        order = orderDAG.OrderDAG(dag_gen, id, 1)
        self._all_orders[id] = order
        order_list.append(order)

    def generate_dynamic_order_introduction_times_uniform(self, deadline):
        for ordr in self._dynamic_orders:
            selected_step = random.randint(1, deadline - 1)
            while selected_step in self._dynamic_orders_intro_steps.keys():
                selected_step = random.randint(1, deadline - 1)
            self._dynamic_orders_intro_steps[selected_step] = ordr
            self._order_intro_times[ordr.get_id()] = selected_step

    def possibly_introduce_dynamic_order(self, step):
        if step in self._dynamic_orders_intro_steps.keys():
            return self._dynamic_orders_intro_steps[step]

    def get_init_orders(self):
        return self._init_orders

    def print_orders(self):
        print("Initial Orders:")
        for order_obj in self._init_orders:
            print(order_obj)
        print("Dynamic Orders:")
        for order_obj in self._dynamic_orders:
            print(order_obj)

    def print_order_completion_times(self):
        print("Order Completion times:")
        for order_id in self._order_intro_times.keys():
            print("Order id %s" % order_id)
            if order_id in self._order_completion_times.keys():
                print("Took %s steps to complete after its introduction" %
                      (self._order_completion_times[order_id] - self._order_intro_times[order_id]))
                print("The priority was %s" % self._all_orders[order_id].get_prio())
            else:
                print("Has not finished yet")
            print("")

    def return_mapping_prio_to_completion_times(self):
        ret = []
        for order_id, completion in self._order_completion_times.items():
            ret.append((self._all_orders[order_id].get_prio(), completion))
        return ret

    def get_order_start_work_times(self):
        return self._order_work_start_times

    def get_order_finish_work_times(self):
        return self._order_completion_times








