import customexceptions
import udptransmit
import utils
import math

class Scheduler:
    def __init__(self, robots: dict, shelves: dict, goals: dict, homes: dict, init_orders: list):
        self._robots = robots
        self._shelves = shelves
        
        self._active_tasks = {}

        self._goals = goals
        self._homes = homes

        self._orders_backlog = []
        self._orders_backlog.extend(init_orders)

        self._orders_active = []

        self._order_robots_assignment = {}
        self._order_goal_assignment = {}

        self._schedule = {}

        self._all_positions = {}
        self._all_distances = {}

        for robot_name, robot_obj in self._robots.items():
            self._all_positions[robot_name] = robot_obj.get_position()

        for shelf_name, shelf_obj in self._shelves.items():
            self._all_positions[shelf_name] = shelf_obj.get_position()

        for goal_name, goal_obj in self._goals.items():
            self._all_positions[goal_name] = goal_obj.get_position()

        self.recalculate_distances()

    def schedule(self):
        """Must be implemented by subclasses"""
        raise NotImplementedError

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
                                                                
    def find_free_robots_and_handle_faults(self):
        """
        Handles robots which have critically faulted.
        RETURNS a list of robots available to take a new task.
        """
        num_critically_faulted = 0
        free_robots = []
        for robot_name, robot in self._robots.items():
            if robot.critically_faulted:
                self.handle_critical_faults(robot)
                num_critically_faulted += 1

                continue

            if robot.is_charging():
                continue

            robot_already_used = False
            for assignment in self._order_robots_assignment.values():
                if robot_name in assignment:
                    robot_already_used = True

            if not robot_already_used:
                free_robots.append(robot)

        if num_critically_faulted == len(self._robots):
            raise customexceptions.SimulationError("All robots have critically faulted, unable to continue.")


        return free_robots
    
    def handle_critical_faults(self, robot_obj):
        """
        Removes robot from any schedules and marks its task as unassigned so it can be rescheduled to a different robot.
        """
        task_id = robot_obj.current_task_id
        if task_id is not None:
            order_id = robot_obj.assigned_order
            order_obj = None
            for o in self._orders_active:
                if o.get_id() == order_id:
                    order_obj = o
            if order_obj is not None:
                order_obj.mark_unassigned(task_id)
                self._active_tasks.pop(f"{task_id}_{order_id}")

            self._schedule[robot_obj.get_name()] = []
            robot_obj.current_task_id = None
            
        task_id = robot_obj.next_task_id
        if task_id is not None:
            order_id = robot_obj.next_assigned_order
            order_obj = None
            for o in self._orders_active:
                if o.get_id() == order_id:
                    order_obj = o
            if order_obj is not None:
                order_obj.mark_unassigned(task_id)

                self._active_tasks.pop(f"{task_id}_{order_id}")

            self._schedule[robot_obj.get_name()] = []
            robot_obj.next_task_id = None

    def add_order(self, order):
        # print("Adding new order %s to backlog" % order.get_id())
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
                    robot_obj.current_task_id = task_id
                    if robot_obj.next_task_id == task_id:
                        robot_obj.next_task_id = None

                if order_id != None:
                    robot_obj.assigned_order = order_id

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

    def handle_complete_order(self, order):
        self._orders_active.remove(order)
        udptransmit.transmit_order_complete()
    
        _ = self._order_robots_assignment.pop(order.get_id())
        self._order_goal_assignment.pop(order.get_id())
        # print("Order %s complete" % order.get_id())

        self.schedule()    

    def get_order_from_backlog(self):
        """
        Gets an order from the backlog and assigns a goal to it.
        Returns None if there are no goals available for the order.
        """
        order = self._orders_backlog[0]
        goal_obj = self.find_goal_for_order(order)
        if goal_obj is None:
            return None

        self._order_goal_assignment[order.get_id()] = goal_obj.get_name()
        goal_obj.set_active_order(order)

        self._orders_backlog.pop(0)
        self._orders_active.append(order)

        return order
    
    def find_goal_for_order(self, order_obj):
        """
        If the order already has an assigned goal, returns that goal, otherwise, returns a free goal.
        """
        if (order_obj.get_id() in self._order_goal_assignment.keys() and order_obj.get_id()
                not in self._order_robots_assignment.keys()):
            goal_name = self._order_goal_assignment[order_obj.get_id()]
            return self._goals[goal_name]
        
        for goal_name, goal in self._goals.items():
            if goal_name not in self._order_goal_assignment.values():
                return goal

        return
        
    def assign_task_with_robot(self, task_id, rank, order_obj, robot_obj):
        if f"{task_id}_{order_obj.get_id()}" in self._active_tasks:
            return False
        
        self._active_tasks[f"{task_id}_{order_obj.get_id()}"] = True
        order_obj.mark_assigned(task_id) 
    
        size = task_id.split("_")[0].lower()
        if size == "small":
            robot_obj.payload_weight = 1.0
        elif size == "medium":
            robot_obj.payload_weight = 2.0
        else:
            robot_obj.payload_weight = 5.0

        robot_obj.next_task_id = task_id
        robot_obj.next_assigned_order = order_obj.get_id()

        goal_name = self._order_goal_assignment.get(order_obj.get_id())
        self.assign_single_robot_schedule_empty_starting_inventory(
            order_obj, robot_obj, self._goals[goal_name], task_id, rank
        )

        return True
    
    def assign_single_robot_schedule_empty_starting_inventory(self, order_obj, robot_obj, goal_obj, task_id, rank):
        robot_name = robot_obj.get_name()
        goal_name = goal_obj.get_name()
        if order_obj.get_id() in self._order_robots_assignment.keys():
            self._order_robots_assignment[order_obj.get_id()].append(robot_name)
        else:
            self._order_robots_assignment[order_obj.get_id()] = [robot_name]
        self._order_goal_assignment[order_obj.get_id()] = goal_name
        robot_obj.prio = rank

        task_data = order_obj.dag.nodes[task_id]
        assigned_shelf = task_data['shelf_name']

        # print(f"Assigning task {task_id} with rank {rank} of order {order_obj.get_id()} to robot {robot_name} at {robot_obj.battery_level}, which will go to shelf {assigned_shelf} and then goal {goal_name}")

        self.add_to_schedule(robot_name, assigned_shelf, task_id, order_obj.get_id())
        
        self.add_to_schedule(robot_name, goal_name, task_id, order_obj.get_id())
        
    def add_to_schedule(self, robot_name, target_name, task_id, order_id):
        if robot_name not in self._schedule.keys():
            self._schedule[robot_name] = []
        self._schedule[robot_name].append([target_name, task_id, order_id])

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

        orders_to_move = []
        for robot_obj in free_robots:
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

                assigned_this_robot = self.assign_task_with_robot(task_id, 0, order_obj, robot_obj)
            
        return orders_to_move

class HeftScheduler(Scheduler):
    def schedule(self):
        free_robots = self.find_free_robots_and_handle_faults()
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
                rank = task_info['rank']
                
                assigned_this_robot = self.assign_task_with_robot(task_id, rank, order_obj, robot_obj)

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
    
class DlsScheduler(Scheduler):
    def schedule(self):
        free_robots = self.find_free_robots_and_handle_faults()
        if not free_robots:
            return

        all_ready_tasks = []
        for order in self._orders_active:
            tasks = order.get_ready_tasks()
            for tid in tasks:
                if f"{tid}_{order.get_id()}" not in self._active_tasks:
                    all_ready_tasks.append({'order': order, 'task_id': tid})

        if len(all_ready_tasks) < len(free_robots) and self._orders_backlog:
            new_order = self.get_order_from_backlog()
            if new_order:
                for tid in new_order.get_ready_tasks():
                    all_ready_tasks.append({'order': new_order, 'task_id': tid})

        while all_ready_tasks and free_robots:
            current_task = all_ready_tasks.pop(0)
            order_obj = current_task['order']
            tid = current_task['task_id']

            best_robot = None
            lowest_cost = math.inf

            task_data = order_obj.dag.nodes[tid]
            shelf_name = task_data['shelf_name']
            shelf_pos = self._shelves[shelf_name].get_position()

            for robot in free_robots:
                dist = utils.taxicab_dist(robot.get_position()[0], robot.get_position()[1], shelf_pos[0], shelf_pos[1])
                reliability_tax = robot.num_faults * 5 
                
                total_cost = dist + reliability_tax

                if total_cost < lowest_cost:
                    lowest_cost = total_cost
                    best_robot = robot

            if best_robot:
                self.assign_task_with_robot(tid, 0, order_obj, best_robot)
                free_robots.remove(best_robot) 
    
class HeftDlsScheduler(Scheduler):
    def schedule(self):
        free_robots = self.find_free_robots_and_handle_faults()
        if not free_robots:
            return
        
        all_ready_tasks = []
        for order in self._orders_active:
            all_ready_tasks.extend(self.get_ready_tasks_with_rank(order))
        
        if len(all_ready_tasks) < len(free_robots) and self._orders_backlog:
            new_order = self.get_order_from_backlog()
            if new_order:
                all_ready_tasks.extend(self.get_ready_tasks_with_rank(new_order))

        all_ready_tasks.sort(key=lambda x: x['rank'], reverse=True)

        while all_ready_tasks and free_robots:
            task_info = all_ready_tasks.pop(0)
            order_obj = task_info['order']
            task_id = task_info['task_id']
            rank = task_info['rank']
            
            best_robot = None
            best_score = math.inf

            for robot in free_robots:
                task_data = order_obj.dag.nodes[task_id]
                shelf_pos = self._shelves[task_data['shelf_name']].get_position()
                dist = utils.taxicab_dist(robot.get_position()[0], robot.get_position()[1], shelf_pos[0], shelf_pos[1])
                
                reliability_penalty = robot.num_faults * 5
                
                fitness_score = dist + reliability_penalty

                if fitness_score < best_score:
                    best_score = fitness_score
                    best_robot = robot

            if best_robot:
                self.assign_task_with_robot(task_id, rank, order_obj, best_robot)
                free_robots.remove(best_robot)
        
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
    

class DynamicHeftDlsScheduler(Scheduler):
    def schedule(self):
        free_robots = self.find_free_robots_and_handle_faults()
        if not free_robots:
            return
        
        all_ready_tasks = []
        for order in self._orders_active:
            all_ready_tasks.extend(self.get_ready_tasks_with_rank(order))
        
        if len(all_ready_tasks) < len(free_robots) and self._orders_backlog:
            new_order = self.get_order_from_backlog()
            if new_order:
                all_ready_tasks.extend(self.get_ready_tasks_with_rank(new_order))

        all_ready_tasks.sort(key=lambda x: x['rank'], reverse=True)

        assigned_tasks_indices = []

        for i, task_info in enumerate(all_ready_tasks):
            if not free_robots:
                break
                
            order_obj = task_info['order']
            task_id = task_info['task_id']
            rank = task_info['rank']
            
            best_robot = None
            best_score = math.inf

            for robot in free_robots:
                if not self.is_capable(robot, task_id):
                    continue

                task_data = order_obj.dag.nodes[task_id]
                shelf_pos = self._shelves[task_data['shelf_name']].get_position()
                dist = utils.taxicab_dist(robot.get_position()[0], robot.get_position()[1], 
                                        shelf_pos[0], shelf_pos[1])
                
                fitness_score = dist + (robot.num_faults * 5)

                if fitness_score < best_score:
                    best_score = fitness_score
                    best_robot = robot

            if best_robot:
                self.assign_task_with_robot(task_id, rank, order_obj, best_robot)
                free_robots.remove(best_robot)
                assigned_tasks_indices.append(i)

        for index in sorted(assigned_tasks_indices, reverse=True):
            all_ready_tasks.pop(index)

        for robot in free_robots:
            if robot.battery_level < 15: # Or your BATTERY_THRESHOLD
                robot.apply_charge_wait_upon_reaching_home = True
                selected_home = self._homes[self.get_home_name_for_robot_name(robot.get_name())]
                self._schedule[robot.get_name()] = [[selected_home.get_name(), None, None]]
        
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

    def is_capable(self, robot_obj, task_id):
        task_type = task_id.split("_")[0].lower()
        battery = robot_obj.battery_level
        
        if task_type == "large":
            return battery >= 25.0
        if task_type == "medium":
            return battery >= 15.0 
        if task_type == "small":
            return battery >= 10.0 
        return False