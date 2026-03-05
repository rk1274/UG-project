import copy
import math


import customexceptions
import gahandler
import ordermanager
import utils
import pygad
import order
import random

class Scheduler:
    def __init__(self, order_manager, robots: dict, shelves: dict, goals: dict, homes: dict, init_orders: list, schedule_mode:str,
                 robot_inventory_size: int,
                 fault_tolerant_mode: bool):
        self._order_manager_ref = order_manager
        self._fault_tolerant_mode = fault_tolerant_mode
        self._robots = robots
        self._num_robots = len(robots.keys())
        self._shelves = shelves
        self._item_to_shelf_mapping = {}
        self._shelf_to_item_mapping = {}

        self._order_to_amount_robots_assigned = {}

        self._schedule_mode = schedule_mode
        self._ga_attempts = [0,0,0,0,0]

        if schedule_mode not in ["simple", "simple-interrupt", "multi-robot", "multi-robot-genetic"]:
            raise customexceptions.SimulationError("Invalid scheduling mode provided")

        for shelf_name, shelf in self._shelves.items():
            item_name = shelf.get_item().get_name()
            self._shelf_to_item_mapping[shelf_name] = shelf.get_item()

            if item_name not in self._item_to_shelf_mapping.keys():
                self._item_to_shelf_mapping[item_name] = [shelf_name]
            else:
                self._item_to_shelf_mapping[item_name] = self._item_to_shelf_mapping[item_name].append(shelf_name)

        self._goals = goals
        self._flags = []
        self._homes = homes

        self._ROBOT_INVENTORY_SIZE = robot_inventory_size

        self._orders_backlog = []
        self._orders_backlog.extend(init_orders)

        self._orders_active = []

        self._order_robots_assignment = {}
        self._order_goal_assignment = {}

        self._schedule = {}

        self._all_positions = {}
        self._all_genes = []
        self._all_distances = {}

        self._mr_flag_ctr = 0

        for robot_name, robot_obj in self._robots.items():
            self._all_positions[robot_name] = robot_obj.get_position()
            self._all_genes.append(robot_name)

        for shelf_name, shelf_obj in self._shelves.items():
            self._all_positions[shelf_name] = shelf_obj.get_position()
            self._all_genes.append(shelf_name)

        for goal_name, goal_obj in self._goals.items():
            self._all_positions[goal_name] = goal_obj.get_position()
            self._all_genes.append(goal_name)

        self.recalculate_distances()

    def get_ga_attempts(self):
        return self._ga_attempts

    def recalculate_distances(self):
        for robot_name, robot_obj in self._robots.items():
            self._all_positions[robot_name] = robot_obj.get_position()

        for location1 in self._all_positions.keys():
            for location2 in self._all_positions.keys():
                if (location2, location1) not in self._all_distances.keys():
                    if (((location1, location2) not in self._all_distances.keys()) or
                            ("robot" in location1) or ("robot" in location2)):
                        if location1 != location2:
                            x1 = self._all_positions[location1][0]
                            y1 = self._all_positions[location1][1]

                            x2 = self._all_positions[location2][0]
                            y2 = self._all_positions[location2][1]

                            self._all_distances[(location1, location2)] = utils.taxicab_dist(x1,y1,x2,y2)

    def add_flag(self, flag: str):
        self._flags.append(flag)

    def schedule(self, step_value):
        #print("SCHEDULING")
        #print("The current backlog is %s" % self._orders_backlog)
        #print("The current active is %s" % self._orders_active)
        #print("The current robot assignment is %s" % self._order_robots_assignment)
        #print("The current goal assignment is %s" % self._order_goal_assignment)

        new_orders = []
        if self._schedule_mode == "simple":
            new_orders = self.simple_single_robot_schedule(self._fault_tolerant_mode)
        elif self._schedule_mode == "simple-interrupt":
            new_orders = self.single_interrupt_robot_schedule(self._fault_tolerant_mode)
        elif self._schedule_mode == "multi-robot":
            new_orders = self.multi_robot_schedule_simple(self._fault_tolerant_mode)
        elif self._schedule_mode == "multi-robot-genetic":
            new_orders = self.multi_robot_schedule_genetic(self._fault_tolerant_mode)

        for order_obj in new_orders:
            self._order_manager_ref.set_order_start_work_time(order_obj.get_id(), step_value)

        #print("AFTER SCHEDULING")
        #print("After, the current backlog is %s" % self._orders_backlog)
        #print("After, the current active is %s" % self._orders_active)
        #print("After, The current robot assignment is %s" % self._order_robots_assignment)
        #print("After, The current goal assignment is %s" % self._order_goal_assignment)
    def get_items_already_delivered_for_order(self, order_id):
        order_goal_name = self._order_goal_assignment[order_id]
        order_goal = self._goals[order_goal_name]
        return order_goal.report_inventory()

    def get_order_to_amount_of_robots_assigned(self):
        return self._order_to_amount_robots_assigned

    def reassign_orders_if_faulted(self):
        orders_to_remove = []
        orders_to_add = []
        for order_id, robot_names in self._order_robots_assignment.items():
            if len(robot_names) == 1:
                robot_obj = self._robots[robot_names[0]]
                if robot_obj.battery_faulted_critical or robot_obj.battery_faulted:
                    self._schedule[robot_names[0]] = []
                    order_to_remove, new_order = self.generate_order_to_complete_fault(order_id)

                    orders_to_remove.append(order_to_remove)
                    orders_to_add.append(new_order)
            else:
                critical_battery_fault_bots = []
                battery_charge_bots = []
                non_faulted_bots = []
                for robot_name in robot_names:
                    robot_obj = self._robots[robot_name]
                    if robot_obj.battery_faulted_critical:
                        critical_battery_fault_bots.append(robot_name)
                    if robot_obj.battery_faulted:
                        battery_charge_bots.append(robot_name)
                    if not robot_obj.battery_faulted_critical and not robot_obj.battery_faulted:
                        non_faulted_bots.append(robot_name)
                    else:
                        self._schedule[robot_name] = []
                if len(critical_battery_fault_bots) > 0 or len(battery_charge_bots) > 0:
                    for robot_name in non_faulted_bots:
                        robot_obj = self._robots[robot_name]
                        robot_obj.gone_home_to_clear_inv = True
                        robot_obj.set_target(self._homes[self.get_home_name_for_robot_name(robot_obj.get_name())])
                        self._schedule[robot_obj.get_name()] = []
                        order_to_remove, new_order = self.generate_order_to_complete_fault(order_id)

                        orders_to_remove.append(order_to_remove)
                        orders_to_add.append(new_order)

        for order_obj in orders_to_remove:
            self._order_robots_assignment.pop(order_obj.get_id())
            self._orders_active.remove(order_obj)

        for order_obj in orders_to_add:
            self._orders_backlog.append(order_obj)


    def generate_order_to_complete_fault(self, order_id):
        items_already_delivered = self.get_items_already_delivered_for_order(order_id)
        order_to_remove = None
        for order_obj in self._orders_active:
            if order_obj.get_id() == order_id:
                order_to_remove = order_obj

        items_left_to_deliver = copy.deepcopy(order_to_remove.get_original_items())

        for item1 in items_already_delivered:
            items_left_to_deliver.remove(item1)

        new_order = order.Order(items_left_to_deliver, order_to_remove.get_prio(),
                                order_to_remove.get_id(), order_to_remove.get_original_items())

        if len(items_already_delivered) == 0:
            self._order_goal_assignment.pop(order_id)

        return order_to_remove, new_order

    def simple_single_robot_schedule(self, fault_tolerant_mode, single_item_mode=False):
        if fault_tolerant_mode:
            self.reassign_orders_if_faulted()

        orders_to_move = []
        # For every order in the backlog (sorted by priority)
        for order_obj in reversed(sorted(self._orders_backlog, key=lambda order1: order1.get_prio())):

            free_robots = self.find_free_robots(fault_tolerant_mode)
            if not free_robots:
                free_robot_obj = None
            else:
                free_robot_obj = free_robots[0]

            free_goal_obj = self.find_goal_for_order(order_obj)

            if (free_robot_obj is not None) and (free_goal_obj is not None):
                self.assign_single_robot_schedule_empty_starting_inventory(order_obj,
                                                                           free_robot_obj,
                                                                           free_goal_obj,
                                                                           single_item_mode)
                orders_to_move.append(order_obj)

        for ordr in orders_to_move:
            self._orders_backlog.remove(ordr)
            self._orders_active.append(ordr)
        return orders_to_move

    def find_free_robots(self, fault_tolerant_mode):
        free_robots = []
        for robot_name, robot in self._robots.items():
            if fault_tolerant_mode:
                # Check if the robot has critically faulted
                if robot.battery_faulted_critical or robot.battery_faulted or robot.gone_home_to_clear_inv:
                    continue
            # Check whether there is a free robot to take the order
            robot_already_used = False
            for assignment in self._order_robots_assignment.values():
                if robot_name in assignment:
                    robot_already_used = True

            if not robot_already_used:
                free_robots.append(robot)
        return free_robots

    def find_goal_for_order(self, order_obj):
        free_goal_obj = None
        # If this order already has an assigned goal
        if (order_obj.get_id() in self._order_goal_assignment.keys() and order_obj.get_id()
                not in self._order_robots_assignment.keys()):
            goal_name = self._order_goal_assignment[order_obj.get_id()]
            #print("preserving goal for order %s" % order_obj.get_id())
            # Then we can use the same goal again
            free_goal_obj = self._goals[goal_name]
        else:
            # Otherwise, for every goal
            for goal_name, goal in self._goals.items():

                # Check whether its being used
                if goal_name not in self._order_goal_assignment.values():
                    free_goal_obj = goal

        return free_goal_obj

    def assign_single_robot_schedule_empty_starting_inventory(self, order_obj, robot_obj, goal_obj, single_item_mode=False):
        robot_name = robot_obj.get_name()
        goal_name = goal_obj.get_name()
        self._order_robots_assignment[order_obj.get_id()] = [robot_name]
        self._order_goal_assignment[order_obj.get_id()] = goal_name
        robot_obj.set_prio(order_obj.get_prio())

        # Get tasks that have no unmet dependencies
        ready_tasks = order_obj.get_ready_tasks()
        
        if not ready_tasks:
            return

        robot_inventory_used = 0

        # In a DAG context, 'item' is likely the node ID in your NetworkX graph
        for task_id in ready_tasks:
            # Assuming the node data contains the actual item/shelf info
            # or that task_id maps to an item name
            task_data = order_obj.dag.nodes[task_id]
            assigned_shelf = task_data['shelf_name']

            if robot_inventory_used == self._ROBOT_INVENTORY_SIZE:
                self.add_to_schedule(robot_name, goal_name)
                robot_inventory_used = 0
            
            self.add_to_schedule(robot_name, assigned_shelf)
            # Mark as assigned so get_ready_tasks() doesn't return it again next time
            order_obj.mark_assigned(task_id)
            robot_inventory_used += 1

        # Final delivery for this batch of ready tasks
        self.add_to_schedule(robot_name, goal_name)

    def add_to_schedule(self, robot_name, target_name):
        if robot_name not in self._schedule.keys():
            self._schedule[robot_name] = []
        self._schedule[robot_name].append(target_name)

    def prepend_to_schedule(self, robot_name, targets_list):
        if robot_name not in self._schedule.keys():
            self._schedule[robot_name] = []
        self._schedule[robot_name] = targets_list + self._schedule[robot_name]

    def add_order(self, order, step_value):
        self._orders_backlog.append(order)
        self.schedule(step_value)

    def direct_robot(self, robot_obj):
        robot_name = robot_obj.get_name()
        if robot_name in self._schedule.keys():
            # We shouldn't do anything if the scheduler has nothing more for this robot
            if self._schedule[robot_name]:
                #print("my schedule was %s" % self._schedule[robot_name])
                robot_next_target_name = self._schedule[robot_name].pop(0)
                #print("popping %s" % robot_next_target_name)
                robot_next_target_obj = self.parse_schedule_value(robot_next_target_name, robot_obj)
                robot_obj.set_target(robot_next_target_obj)
            else:
                for robot_assignment in self._order_robots_assignment.values():
                    if robot_name in robot_assignment:
                        robot_assignment.remove(robot_name)
                        # homeN is robotN's home
                #print("setting %s to return home" % robot_name)
                selected_home = self._homes[self.get_home_name_for_robot_name(robot_name)]
                self._schedule[robot_name] = [selected_home.get_name()]

    def parse_schedule_value(self, robot_next_target_name, robot_obj):
        robot_next_target_obj = None
        dest_type = robot_next_target_name.split("|")[0]
        if "shelf" in dest_type:
            robot_next_target_obj = self._shelves[robot_next_target_name]
        elif "goal" in dest_type:
            if "|" in robot_next_target_name:
                if "flag" in robot_next_target_name:
                    goal_name = robot_next_target_name.split("|")[0]
                    flag_name = robot_next_target_name.split("|")[1]
                    robot_next_target_obj = self._goals[goal_name]
                    robot_obj.set_flag(flag_name)
                else:
                    goal_name = robot_next_target_name.split("|")[0]
                    amount_items = int(robot_next_target_name.split("|")[1])

                    robot_next_target_obj = self._goals[goal_name]
                    robot_obj.set_amount_of_items_to_transfer_next_time(amount_items)
            else:
                robot_next_target_obj = self._goals[robot_next_target_name]
        elif "home" in dest_type:
            robot_next_target_obj = self._homes[robot_next_target_name]
        elif "block" in dest_type:
            split = robot_next_target_name.split("|")
            flag_name = split[1]

            if flag_name in self._flags:
                robot_next_target_obj = self.parse_schedule_value(self._schedule[robot_obj.get_name()].pop(0), robot_obj)
            else:
                robot_next_target_obj = self._homes[self.get_home_name_for_robot_name(robot_obj.get_name())]
                self.prepend_to_schedule(robot_obj.get_name(), [robot_next_target_name])
        elif "wait" in dest_type:
            robot_next_target_obj = self._homes[self.get_home_name_for_robot_name(robot_obj.get_name())]
            robot_obj.add_wait_steps(2)

        if robot_next_target_obj is None:
            message = "Invalid target %s in schedule for robot %s" % (robot_next_target_name, robot_obj.get_name())
            raise customexceptions.SimulationError(message)

        return robot_next_target_obj

    def get_home_name_for_robot_name(self, robot_name):
        return "home%s" % robot_name[5:]

    def are_all_orders_complete(self):
        if self._orders_backlog:
            return False
        if self._orders_active:
            return False
        return True

    def is_this_a_complete_order(self, items: list, order_manager: ordermanager.OrderManager, robot_obj, goal_name, step_ctr):
        for order in self._orders_active:
            comp_items = copy.deepcopy(items)
            should_continue = False
            for order_item in order.get_original_items():
                if order_item not in comp_items:
                    should_continue = True
                    break
                else:
                    comp_items.remove(order_item)

            if should_continue:
                continue

            if len(comp_items) == 0 and robot_obj.get_name() in self._order_robots_assignment[order.get_id()] and goal_name == self._order_goal_assignment[order.get_id()]:

                self._orders_active.remove(order)

                robots = self._order_robots_assignment.pop(order.get_id())
                self._order_goal_assignment.pop(order.get_id())
                #print("Order %s completed by robot %s" % (order.get_id(), robots))
                #print("order %s complete" % order.get_id())
                order_manager.set_order_completion_time(order, step_ctr)

                self.schedule(step_ctr)

                return True
        return False












