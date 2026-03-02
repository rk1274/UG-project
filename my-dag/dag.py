import networkx as nx
import os
import random
import argparse
from enum import Enum

class Size(Enum):
    LARGE = 4
    MEDIUM = 2
    SMALL = 1

class Task:
    def __init__(self, size, task_id):
        self.size = size
        self.id = task_id
        self.node_id = f"{size.name}_{task_id}"
        # TODO - make weights better
        self.weight = size.value * 5 + random.randint(1, 5) 

class Order:
    def __init__(self, num_large, num_medium, num_small):
        self.num_large = num_large
        self.num_medium = num_medium
        self.num_small = num_small
        self.name = f"L{num_large}_M{num_medium}_S{num_small}_{random.randint(100,999)}"
        self.tasks = self._make_tasks()

    def _make_tasks(self):
        tasks = []
        for i in range(self.num_large): tasks.append(Task(Size.LARGE, i))
        for i in range(self.num_medium): tasks.append(Task(Size.MEDIUM, i + self.num_large))
        for i in range(self.num_small): tasks.append(Task(Size.SMALL, i + self.num_large + self.num_medium))
        
        return tasks

    def generate_dag(self):
        G = nx.DiGraph()
        
        all_tasks = sorted(self.tasks, key=lambda x: x.size.value, reverse=True)

        for t in all_tasks:
            G.add_node(t.node_id, weight=t.weight, size=t.size.name)

        base = all_tasks[0]
        remaining_tasks = all_tasks[1:]
        processed_tasks = [base]

        for task in remaining_tasks:
            potential_parents = [p for p in processed_tasks if p.size.value >= task.size.value]

            if not potential_parents:
                parents = [base]
            else:
                if random.random() > 0.75 and len(potential_parents) >= 2:
                    parents = random.sample(potential_parents, 2)
                else:
                    parents = [random.choice(potential_parents)]

            if task.size != Size.LARGE:
                large_parent_objects = [p for p in parents if p.size == Size.LARGE]
                
                if large_parent_objects:
                    needed = set() 
                    
                    for lp in large_parent_objects:
                        relatives = self.get_large_relatives(G, lp.node_id)
                        needed.update(relatives)

                    for node_id in needed:
                        rel_task = next((t for t in self.tasks if t.node_id == node_id), None)
                        
                        if rel_task and rel_task not in parents:
                            parents.append(rel_task)

            for p in parents:
                p_id = p.node_id if hasattr(p, 'node_id') else p
                G.add_edge(p_id, task.node_id)
            
            processed_tasks.append(task)

        leaves = [n for n in G.nodes() if G.out_degree(n) == 0]
        G.add_node("SINK", weight=0, size="VIRTUAL")
        for leaf in leaves:
            G.add_edge(leaf, "SINK")

        self.dag = G

    def get_large_relatives(self, G, node_id):
        large_children = {n for n in G.successors(node_id) 
                        if G.nodes[n].get('size') == "LARGE"}

        large_siblings = {s for p in G.predecessors(node_id) 
                        for s in G.successors(p) 
                        if G.nodes[s].get('size') == "LARGE" and s != node_id}

        combined = large_children | large_siblings
        
        return list(combined)

    def get_simple_list(self):
        simple_queue = list(nx.lexicographical_topological_sort(self.dag))
        
        if "SINK" in simple_queue:
            simple_queue.remove("SINK")
            
        return simple_queue
        
    def save(self):
        print("Saving...")

        A = nx.nx_agraph.to_agraph(self.dag)

        A.layout(prog='dot')

        if not os.path.exists("./data/"):
            os.makedirs("./data/")

        A.draw("./data/" + "dag_" + self.name + '.png', format="png")
        
        nx.write_gml(self.dag, "./data/" + "dag_" + self.name + '.gml')

        print(f"{self.name}:{self.get_simple_list()}")

def generate_random_order():
    large = random.randrange(1,10)
    medium = random.randrange(1,10)
    small = random.randrange(1,10)
    order =  Order(large,medium,small)

    return order

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a DAG from task counts.")

    parser.add_argument("--large", type=int, default=2, help="Number of large tasks")
    parser.add_argument("--medium", type=int, default=5, help="Number of medium tasks")
    parser.add_argument("--small", type=int, default=3, help="Number of small tasks")
    parser.add_argument("--random", type=bool, default=False, help="Generate a random order")

    args = parser.parse_args()

    if args.random:
        order = generate_random_order()
    else: 
        order = Order(args.large, args.medium, args.small)

    order.generate_dag()

    order.save()
