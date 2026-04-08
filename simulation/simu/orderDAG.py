class OrderDAG:
    def __init__(self, dag_graph, ranks, id):
        self.dag = dag_graph
        self.completed_tasks = set()
        self.assigned_tasks = set()
        self.id = id
        self.ranks = ranks
    
    def get_id(self):
        return self.id

    def get_ready_tasks(self):
        """
        Returns tasks that have 0 incoming edges OR all parents are completed.
        This allows for parallel execution of independent branches.
        """
        ready = []
        for node in self.dag.nodes():
            if node == "SINK" or node in self.completed_tasks or node in self.assigned_tasks:
                continue
            
            # Check if all predecessors (parents) are in the completed_tasks set
            parents = list(self.dag.predecessors(node))
            if all(p in self.completed_tasks for p in parents):
                ready.append(node)
        return ready
    
    def mark_assigned(self, task_id):
        self.assigned_tasks.add(task_id)

    def mark_unassigned(self, task_id):
        self.assigned_tasks.remove(task_id)

    def mark_completed(self, task_id):
        self.assigned_tasks.remove(task_id)
        self.completed_tasks.add(task_id)

    def is_completed(self, task_id):
        return task_id in self.completed_tasks

    def is_finished(self):
        # The mission is done when the only thing left is the VIRTUAL SINK
        non_virtual_nodes = [n for n in self.dag.nodes() if n != "SINK"]
        return len(self.completed_tasks) == len(non_virtual_nodes)
    
    def get_upward_ranks(self):
        return self.ranks