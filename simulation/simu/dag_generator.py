import networkx as nx
import os
import random
import argparse
import utils

class Task:
    def __init__(self, size, task_id, assigned_shelf_name, shelf_pos, goal_pos):
        self.size = size
        self.id = task_id
        self.node_id = f"{size.name}_{task_id}"
        self.shelf_name = assigned_shelf_name

        distance = utils.taxicab_dist(shelf_pos[0], shelf_pos[1], goal_pos[0], goal_pos[1])
        # Base weight on size + physical distance weighting
        self.weight = (size.value * 10) + (distance * 0.5) + random.randint(1, 5)

class Order:
    def __init__(self, num_large, num_medium, num_small,
                 size_to_shelves_map, shelves_registry, goal_pos):
        self.num_large = num_large
        self.num_medium = num_medium
        self.num_small = num_small
        self.size_to_shelves_map = size_to_shelves_map # e.g., {"LARGE": ["shelf0", "shelf1"]}
        self.shelves_registry = shelves_registry     # The actual shelf objects to get positions
        self.goal_pos = goal_pos
        self.name = f"L{num_large}_M{num_medium}_S{num_small}_{random.randint(100,999)}"
        self.tasks = self._make_tasks()

        self.list = []

    def _make_tasks(self):
        tasks = []
        counts = {
            utils.Size.LARGE: self.num_large,
            utils.Size.MEDIUM: self.num_medium,
            utils.Size.SMALL: self.num_small
        }
        
        total_idx = 0
        for size, count in counts.items():
            for i in range(count):
                # Randomly pick between the two available shelves for this size
                possible_shelves = self.size_to_shelves_map[size]
                chosen_shelf_name = random.choice(possible_shelves)
                shelf_obj = self.shelves_registry[chosen_shelf_name]
                
                tasks.append(Task(
                    size, 
                    total_idx, 
                    chosen_shelf_name, 
                    shelf_obj.get_position(), 
                    self.goal_pos
                ))
                total_idx += 1

        return tasks

    def generate_dag(self):
        G = nx.DiGraph()
        
        all_tasks = sorted(self.tasks, key=lambda x: x.size.value, reverse=True)

        for t in all_tasks:
            G.add_node(t.node_id, weight=t.weight, size=t.size.name, shelf_name=t.shelf_name)

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

            if task.size != utils.Size.LARGE:
                large_parent_objects = [p for p in parents if p.size == utils.Size.LARGE]
                
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

        self.list = processed_tasks

        self.ranks = compute_upward_ranks(G)

    def get_large_relatives(self, G, node_id):
        descendants = set()
    
        for d in nx.descendants(G, node_id):
            if G.nodes[d].get('size') == "LARGE":
                descendants.add(d)
                
        siblings = set()
        for p in G.predecessors(node_id):
            for s in G.successors(p):
                if s != node_id and G.nodes[s].get('size') == "LARGE":
                    siblings.add(s)
                    # siblings.update(n for n in nx.descendants(G, s) if G.nodes[n].get('size') == "LARGE")

        return list(descendants | siblings)
        
    def save(self, name):
        if not os.path.exists(f"./{utils.DAG_FOLDER}/"):
            os.makedirs(f"./{utils.DAG_FOLDER}/")

        try:
            pydot_graph = nx.drawing.nx_pydot.to_pydot(self.dag)
            
            pydot_graph.set_prog('dot')

            pydot_graph.write_png(f"./{utils.DAG_FOLDER}/dag_{name}.png")
            
        except Exception as e:
            print(f"Drawing failed, but saving data anyway. Error: {e}")

        nx.write_gml(self.dag, f"./{utils.DAG_FOLDER}/dag_{name}.gml")
    
def compute_upward_ranks(dag):
    """Calculates rank_u for each node in the DAG."""
    ranks = {}
    
    nodes = list(nx.topological_sort(dag))
    for node in reversed(nodes):
        weight = dag.nodes[node].get('weight', 0)
        
        successors = list(dag.successors(node))
        if not successors:
            ranks[node] = weight
        else:
            ranks[node] = weight + max(ranks[s] for s in successors)

    return ranks

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
