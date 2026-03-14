import scheduler

class SimpleScheduler(scheduler.SchedulerOLD):
    def schedule(self):
        return self.simple_single_robot_schedule(self._fault_tolerant_mode)

    def simple_single_robot_schedule(self, fault_tolerant_mode):
        free_robots = self.find_free_robots(fault_tolerant_mode)
        if not free_robots:
            return

        # Collect EVERY task that is currently "Ready" across ALL active orders
        all_ready_tasks = []
        for order_obj in self._orders_active:
            tasks = order_obj.get_ready_tasks() # Tasks with dependencies met
            for tid in tasks:
                if f"{tid}_{order_obj.get_id()}" in self._active_tasks:
                    continue
                # Store as (priority, order_id, task_id)
                all_ready_tasks.append((order_obj, tid))
            
            # if len(tasks) == 0:
            #     print("NO READY TASKS for order with id %s" % order_obj.get_id())

        # TODO MAYBE SORT READY TASKS

        orders_to_move = []
        for robot_obj in free_robots:
            if not all_ready_tasks:
                if not self._orders_backlog:
                    break

                new_order = self._orders_backlog[0]
                # print("\n\n\n\n Introducing new order %s from backlog \n\n\n" % new_order.get_id())
                goal_obj = self.find_goal_for_order(new_order)
                if goal_obj == None:
                    break

                self._order_goal_assignment[new_order.get_id()] = goal_obj.get_name()
                goal_obj.set_active_order(new_order)

                self._orders_active.append(new_order)
                tasks = new_order.get_ready_tasks()
                for tid in tasks:
                    all_ready_tasks.append((new_order, tid))

                orders_to_move.append(new_order)
                _ = self._orders_backlog.pop(0)

            order_obj, task_id = all_ready_tasks.pop(0)
            # TODO this is a simple fix for a race condition but pls do something better!!!
            if f"{task_id}_{order_obj.get_id()}" in self._active_tasks:
                continue
            self._active_tasks[f"{task_id}_{order_obj.get_id()}"] = True
            order_obj.mark_assigned(task_id)
            # print("\n",robot_obj.get_name(),"is taking:", task_id,"for order",order_obj.get_id(),"\n")

            goal_name = self._order_goal_assignment.get(order_obj.get_id())
            goal_obj = self._goals[goal_name]

            self.assign_single_robot_schedule_empty_starting_inventory(
                        order_obj, robot_obj, goal_obj, task_id
                    )
            
        return orders_to_move

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

        self.add_to_schedule(robot_name, assigned_shelf, task_id)
        
        self.add_to_schedule(robot_name, goal_name, task_id)
