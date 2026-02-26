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
    def __init__(self, size, id):
        self.size = size
        self.id = id

class Order:
    def __init__(self, num_large, num_medium, num_small):
        self.name = f"{num_large}_{num_medium}_{num_small}"
        self.num_large = num_large
        self.num_medium = num_medium
        self.num_small = num_small

        self.original_order = []
        for i in range(num_large):
            self.original_order.append(Size.LARGE)
        
        for i in range(num_medium):
            self.original_order.append(Size.MEDIUM)
        
        for i in range(num_small):
            self.original_order.append(Size.SMALL)

        self.order = self.make_order()

    def make_order(self):
        order = []

        for i in range(self.num_large):
            order.append(Task(Size.LARGE, i))
        
        for i in range(self.num_medium):
            order.append(Task(Size.MEDIUM, i+self.num_large))
            
        for i in range(self.num_small):
            order.append(Task(Size.SMALL, i+self.num_large+self.num_medium))

        return order

    def get_total(self):
        return self.num_large + self.num_medium + self.num_small

    def get_largest(self):
        return self.order[0]
    
    def remove(self, task):
        self.order.remove(task)
        
        match task.size:
            case Size.LARGE:
                self.num_large -= 1
                return
            case Size.MEDIUM:
                self.num_medium -= 1
                return
            case Size.SMALL:
                self.num_small -= 1
                return
            
    def generate_dag(self):
        G = nx.DiGraph()

        rank = 0
        root = self.get_largest()
        root_id = f"{root.size.name}_{root.id}"
        G.add_node(root_id, rank=rank)

        self.remove(root)
        current_parents = [root]

        while self.get_total() > 0 and current_parents:
            rank += 1
            next_parents = []

            for parent in current_parents:
                size_remaining = parent.size.value

                for task in self.order[:]:
                    if task.size.value <= size_remaining:
                        node_id = f"{task.size.name}_{task.id}"

                        G.add_node(node_id, rank=rank)
                        G.add_edge(
                            f"{parent.size.name}_{parent.id}",
                            node_id
                        )

                        next_parents.append(task)
                        self.remove(task)

                        size_remaining -= task.size.value

            current_parents = next_parents

        self.dag = G
        
    def save(self):
        print("Saving...")

        A = nx.nx_agraph.to_agraph(self.dag)

        A.layout(prog='dot')

        if not os.path.exists("./data/"):
            os.makedirs("./data/")

        A.draw("./data/" + "dag_" + self.name + '.png', format="png")
        
        nx.write_gml(self.dag, "./data/" + "dag_" + self.name + '.gml')

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
