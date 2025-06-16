# power-system-simulation

This Python package enables users to analyze low-voltage (LV) grids using power flow simulations and graph-based methods. It is the result of three combined assignments and offers functionalities to analyse the impact of electric vehicle (EV) penetration, optimize transformer tap settings, and perform N-1 contingency analysis.

The package integrates:
- Graph processing (Assignment 1)
- Time-series power flow (Assignment 2)
- LV grid analytics (Assignment 3)

## Functionalities

### 1. EV Penetration Analysis
Analyses how a user-defined percentage of houses with EVs charged at home influences the grid. EV charging profiles are randomly assigned to houses in each LV feeder.

- Adds EV load to a subset of sym_loads
- Ensures load ID and timestamp consistency
- Re-runs power flow and returns updated voltage and line summaries

### 2. Optimal Tap Position
Finds the transformer tap setting that:
- Minimizes **total energy loss** in the grid
- Or minimizes **voltage deviation** from 1.0 p.u. across all nodes

### 3. N-1 Line Contingency
Analyzes the grid behavior if a given line is out of service.
- Identifies alternative lines
- Runs power flow for each reconnection
- Outputs a table with output summaries of all alternative scenarios

## Input Data

The user must provide the following input files:

- `pgm_grid.json` (PGM format grid structure)
- `meta_data.json` (additional network metadata)
- `p_profile.parquet` (active power load profile per sym_load)
- `q_profile.parquet` (reactive power profile per sym_load)
- `ev_profile_pool.parquet` (EV charging profile pool, only for EV Penetration Analysis)


### Constraints:
- Grid must have exactly one source and one transformer
- Grid must be connected and cycle-free in its initial state
- Power profiles must align in both timestamps and load IDs
- EV profile pool must be large enough (≥ number of sym_loads)

## Usage Example
An example of the usage of the EV Penetration Analysis functionality:

```python
from power_system_simulation import PowerGrid, ev_penetration_level

grid = PowerGrid(
    pgm_path="input_network_data.json",
    meta_data_path="meta_data.json",
    p_profile_path="active_power_profile.parquet",
    q_profile_path="reactive_power_profile.parquet"
)

# Analyze EV penetration at 50%
voltage_summary, line_summary = ev_penetration_level(
    grid, "ev_active_power_profile.parquet", penetration_level=0.5, seed=42
)
```

## Internal Structure

- `graph_processing.py`: Contains functionalities for processing and validating low-voltage (LV) power grid data graphs.
- `power_grid_calculation.py`: Contains the `PowerGrid` class and related functions for simulating and analyzing low-voltage (LV) power grids using time-series power flow analysis.
- `input_data_validation.py`, `exceptions.py`: Contains function for input validations and raised expections.

## Installation

In a Python environment, in the root of the repository, install it in develop mode using the command below.

**NOTE: you need to re-run the following command everytime you add new (optional) dependencies!**

```shell
pip install -e .[dev,example]
```

After installation, run the test.

```shell
pytest
```

## Code style and quality check

You can run the following two commands to automatically format your code style.

```shell
isort .
black .
```

You can run the following command to check the code quality.
It will return errors if the quality check fails.
You need to read the errors and make required adjustments.

```shell
pylint power_system_simulation 
```

## Folder structure of the repository

The folder structure of the repository is explained as below.


* [`src/power_system_simulation`](./src/power_system_simulation) is the main folder of the package. You should put your new functionality code there.
* [`tests`](./tests) is the folder containing the test files. You should put your test code there.
* [`example`](./example) contains the example notebook. You should modify the notebook for your presentation.
* [`.vscode`](./.vscode) contains the setting file for the IDE VSCode.
* [`.github/workflows`](./.github/workflows) contains the continuous integration (CI) configurations.
