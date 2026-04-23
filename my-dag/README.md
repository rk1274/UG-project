# Warehouse Order DAG Generator
A python program for generating DAGs that represent realistic warehouse orders.

## Requirements
The generator requires Python 3.11+ and the following libraries:
- networkx
- pydot

## Usage
You can generate a specific order by providing task counts or generate a randomised order.
- `--large` : int for the number of large tasks in the order
- `--medium` : int for the number of medium tasks in the order
- `--small` : int for the number of small tasks in the order
- `--random` : boolean to say if you want it random.