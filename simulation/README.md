# RobotWarehouse
A python simulator for a robotic smart warehouse, with many configurable properties.

## Project Structure

- simu/: simulator (Python)
- viz/: visualisor (Unity)

## Requirements

Simulation:

- Python >= 3.11
- pygad
- matplotlib
- networkx
- pydot

Visualisation:

- Unity == 6000..0.41f1

## Usage

To run the simulation, navigate to the simu/ directory and execute main.py
`python main.py [OPTIONS]`

The following CLI options are available:
- `-h`: Shows help text
- `-t`: To use communicate with Unity visualiser
- `-p`: Save representations of the generated DAGs (.png and .gml) to simu/data/
- `-d`: Use premade dags stored inside simu/data/ for the simulation (.gml files required) 
- `-s`: Choose which scheduler to use: 'simple', 'heft', 'dls', 'heft-dls', 'heft-dls-dyn' (default 'simple')
- `-f`: Specify the path to the warehouse layout file
- `-r`: Set the random seed

To use to visualiser you need to open the project in Unity and run the main scene, then run `python main.py -t [OPTIONS]`.

To run experiments, use `python generate_experiment_data.py`. This will save csvs in simu/results/.

### Examples
1. Basic simulation with visualisation enabled:
`python main.py -t`

2. Using the HEFT-DLS hybrid scheduler with a specific random seed:
`python main.py -s heft -r 1234`

3. Using a different warehouse file:
`python main.py -f whouses/whouse_2s_2o_6r.txt`
