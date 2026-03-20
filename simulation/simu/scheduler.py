import copy

import customexceptions
import ordermanager
import orderDAG
import utils
import networkx as nx


class Scheduler:
    def __init__(self, order_manager, robots: dict, shelves: dict, goals: dict, homes: dict, init_orders: list,
                 robot_inventory_size: int,
                 fault_tolerant_mode: bool):
        self._order_manager_ref = order_manager
        self._fault_tolerant_mode = fault_tolerant_mode
        self._robots = robots
        self._num_robots = len(robots.keys())
        self._shelves = shelves
        self._item_to_shelf_mapping = {}
        self._shelf_to_item_mapping = {}
        
        self._active_tasks = {}

        self._order_to_amount_robots_assigned = {}

        self._ga_attempts = [0,0,0,0,0]

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

    def schedule(self):
        """Must be implemented by subclasses"""
        raise NotImplementedError
    
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

        new_order = orderDAG.OrderDAG(items_left_to_deliver, order_to_remove.get_prio(),
                                order_to_remove.get_id(), order_to_remove.get_original_items())

        if len(items_already_delivered) == 0:
            self._order_goal_assignment.pop(order_id)

        return order_to_remove, new_order
                                                                
    def find_free_robots_and_handle_faults(self, fault_tolerant_mode=False):
        free_robots = []
        for robot_name, robot in self._robots.items():
            if robot.has_critically_faulted():
                self.handle_critical_faults(robot)

                continue

            if robot.is_charging():
                continue

            # Check whether there is a free robot to take the order
            robot_already_used = False
            for assignment in self._order_robots_assignment.values():
                if robot_name in assignment:
                    robot_already_used = True

            if not robot_already_used:
                free_robots.append(robot)

        return free_robots
    
    def handle_critical_faults(self, robot_obj):
        task_id = robot_obj.get_task_id()
        if task_id is not None:
            order_id = robot_obj.get_assigned_order()
            order_obj = None
            for o in self._orders_active:
                if o.get_id() == order_id:
                    order_obj = o
            if order_obj is not None:
                order_obj.mark_unassigned(task_id)
                self._active_tasks.pop(f"{task_id}_{order_id}")

            self._schedule[robot_obj.get_name()] = []
            robot_obj.set_task_id(None)

            self.check_if_blocking(robot_obj)

    def check_if_blocking(self, robot_obj):
        x = robot_obj.get_position()[0]
        y = robot_obj.get_position()[1]

        for goal_name, goal_obj in self._goals.items():
            if goal_obj.get_position() == (x,y):
                raise customexceptions.FaultBlockingError(robot_obj.get_name(), goal_name)

        for shelf_name, shelf_obj in self._shelves.items():
            if shelf_obj.get_position() == (x,y):
                raise customexceptions.FaultBlockingError(robot_obj.get_name(), shelf_name)

        for home_name, home_obj in self._homes.items():
            if home_obj.get_robot_name() == robot_obj.get_name():
                continue
            if home_obj.get_position() == (x,y):
                raise customexceptions.FaultBlockingError(robot_obj.get_name(), home_name)


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

    def add_to_schedule(self, robot_name, target_name, task_id, order_id):
        if robot_name not in self._schedule.keys():
            self._schedule[robot_name] = []
        self._schedule[robot_name].append([target_name, task_id, order_id])

    def prepend_to_schedule(self, robot_name, targets_list):
        if robot_name not in self._schedule.keys():
            self._schedule[robot_name] = []
        self._schedule[robot_name] = targets_list + self._schedule[robot_name]

    def add_order(self, order, step_value):
        print("Adding new order %s to backlog" % order.get_id())
        self._orders_backlog.append(order)
        self.schedule()

    def direct_robot(self, robot_obj):
        robot_name = robot_obj.get_name()
        if robot_name in self._schedule.keys():
            # We shouldn't do anything if the scheduler has nothing more for this robot
            if self._schedule[robot_name]:
                #print("my schedule was %s" % self._schedule[robot_name])

                robot_next_target_name, task_id, order_id = self._schedule[robot_name].pop(0)

                #print("popping %s" % robot_next_target_name)
                robot_next_target_obj = self.parse_schedule_value(robot_next_target_name, robot_obj)
                robot_obj.set_target(robot_next_target_obj)
                if task_id != None:
                    robot_obj.set_task_id(task_id)

                if order_id != None:
                    robot_obj.set_assigned_order(order_id)

            else:
                for robot_assignment in self._order_robots_assignment.values():
                    if robot_name in robot_assignment:
                        robot_assignment.remove(robot_name)
                        # homeN is robotN's home
                #print("setting %s to return home" % robot_name)
                selected_home = self._homes[self.get_home_name_for_robot_name(robot_name)]
                self._schedule[robot_name] = [[selected_home.get_name(), None, None]]

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
            # for order in self._orders_active:
                # print("Orders still active: %s" % order.get_id())
            return False
        return True

    def handle_complete_order(self, order_manager: ordermanager.OrderManager, step_ctr, order):
        self._orders_active.remove(order)

        _ = self._order_robots_assignment.pop(order.get_id())
        self._order_goal_assignment.pop(order.get_id())
        #print("Order %s completed by robot %s" % (order.get_id(), robots))
        print("Order %s complete" % order.get_id())
        order_manager.set_order_completion_time(order, step_ctr)

        self.schedule()

    def assign_single_robot_schedule_empty_starting_inventory(self, order_obj, robot_obj, goal_obj, task_id):
        robot_name = robot_obj.get_name()
        goal_name = goal_obj.get_name()
        self._order_robots_assignment[order_obj.get_id()] = [robot_name]
        self._order_goal_assignment[order_obj.get_id()] = goal_name
        robot_obj.set_prio(order_obj.get_prio())

        # Assuming the node data contains the actual item/shelf info
        # or that task_id maps to an item name
        task_data = order_obj.dag.nodes[task_id]
        assigned_shelf = task_data['shelf_name']

        self.add_to_schedule(robot_name, assigned_shelf, task_id, order_obj.get_id())
        
        self.add_to_schedule(robot_name, goal_name, task_id, order_obj.get_id())

    def get_order_from_backlog(self):
        order = self._orders_backlog[0]
        goal_obj = self.find_goal_for_order(order)
        if goal_obj is None:
            return None

        self._order_goal_assignment[order.get_id()] = goal_obj.get_name()
        goal_obj.set_active_order(order)

        self._orders_backlog.pop(0)
        self._orders_active.append(order)

        return order
        
    def assign_task_with_robot(self, task_id, order_obj, robot_obj):
        if f"{task_id}_{order_obj.get_id()}" in self._active_tasks:
            return False
        
        self._active_tasks[f"{task_id}_{order_obj.get_id()}"] = True
        order_obj.mark_assigned(task_id)
    
        size = task_id.split("_")[0].lower()
        if size == "small":
            robot_obj.set_payload_weight(1.0)
        elif size == "medium":
            robot_obj.set_payload_weight(2.0)
        else:
            robot_obj.set_payload_weight(5.0)

        goal_name = self._order_goal_assignment.get(order_obj.get_id())
        self.assign_single_robot_schedule_empty_starting_inventory(
            order_obj, robot_obj, self._goals[goal_name], task_id
        )

        return True

class SimpleScheduler(Scheduler):
    def schedule(self):
        free_robots = self.find_free_robots_and_handle_faults()
        if not free_robots:
            return
        
        all_ready_tasks = []
        for order_obj in self._orders_active:
            tasks = order_obj.get_ready_tasks() 
            for tid in tasks:
                if f"{tid}_{order_obj.get_id()}" in self._active_tasks:
                    continue

                all_ready_tasks.append((order_obj, tid))
            
        # TODO MAYBE SORT READY TASKS

        orders_to_move = []
        for robot_obj in free_robots:
            if robot_obj.get_battery_level() <= utils.BATTERY_THRESHOLD:
                print("Battery low for robot %s, sending home to charge" % robot_obj.get_name(), "Battery level was %s" % robot_obj.get_battery_level())
                robot_obj.apply_charge_wait_upon_reaching_home = True
                selected_home = self._homes[self.get_home_name_for_robot_name(robot_obj.get_name())]
                self._schedule[robot_obj.get_name()] = [[selected_home.get_name(), None]]

                continue

            if not all_ready_tasks:
                if not self._orders_backlog:
                    break

                new_order = self.get_order_from_backlog()
                if new_order == None:
                    break

                tasks = new_order.get_ready_tasks()
                for tid in tasks:
                    all_ready_tasks.append((new_order, tid))

            assigned_this_robot = False
            while all_ready_tasks and not assigned_this_robot:
                order_obj, task_id = all_ready_tasks.pop(0)
                
                assigned_this_robot = self.assign_task_with_robot(task_id, order_obj, robot_obj)
            
        return orders_to_move

class HeftScheduler(Scheduler):
    def schedule(self):
        free_robots = self.find_free_robots_and_handle_faults(self._fault_tolerant_mode)
        if not free_robots:
            return
        
        all_ready_tasks = []
        for order in self._orders_active:
            all_ready_tasks.extend(self.get_ready_tasks_with_rank(order))

        all_ready_tasks.sort(key=lambda x: x['rank'], reverse=True)

        orders_to_move = []
        for robot_obj in free_robots:
            if not all_ready_tasks:
                if not self._orders_backlog:
                    break

                new_order = self.get_order_from_backlog()
                if new_order == None:
                    break

                orders_to_move.append(new_order)

                all_ready_tasks.extend(self.get_ready_tasks_with_rank(new_order))
                all_ready_tasks.sort(key=lambda x: x['rank'], reverse=True)    

            assigned_this_robot = False
            while all_ready_tasks and not assigned_this_robot:
                task_info = all_ready_tasks.pop(0)
                order_obj = task_info['order']
                task_id = task_info['task_id']
                
                assigned_this_robot = self.assign_task_with_robot(task_id, order_obj, robot_obj)

        return orders_to_move
        
    def get_ready_tasks_with_rank(self, order):
        ready_tasks = []
        ranks = order.get_upward_ranks()
        ready_ids = order.get_ready_tasks()
        for tid in ready_ids:
            if f"{tid}_{order.get_id()}" not in self._active_tasks:
                ready_tasks.append({
                    'order': order,
                    'task_id': tid,
                    'rank': ranks.get(tid, 0)
                })

        return ready_tasks
    
