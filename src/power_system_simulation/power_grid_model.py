import json
import numpy as np
import pandas as pd

from power_grid_model import LoadGenType, ComponentType, DatasetType, ComponentAttributeFilterOptions
from power_grid_model import PowerGridModel, CalculationMethod, CalculationType
from power_grid_model import initialize_array, attribute_dtype
from power_grid_model.utils import assert_valid_batch_data, ValidationException
from power_grid_model.utils import json_deserialize, json_serialize

class TimeSeriesPowerFlow:
    def __init__(
            self, 
            pgm_path: str, 
            p_path: str, 
            q_path: str
        ):

        # Load grid 
        with open(pgm_path, "r") as file:
            self.grid_data = json_deserialize(json.load(file))

        # Load profile data
        self.p_profile = pd.read_parquet(p_path)
        self.q_profile = pd.read_parquet(q_path)

        # Validate profiles
        if not self.p_profile.index.equals(self.q_profile.index):
            raise ValueError("Timestamps do not match between p and q profiles.")
        if not self.p_profile.columns.equals(self.q_profile.columns):
            raise ValueError("Load IDs do not match between p and q profiles.")

        # Create model
        self.model = PowerGridModel(self.grid_data)

        # Placeholder for batch output
        self.batch_output = None

    def run(self, method):
        # TODO: Create update_data using initialize_array and the profiles
        # TODO: Validate batch data and run power flow calculation
        pass

    def get_voltage_summary(self):
        # TODO: Aggregate max/min voltage and corresponding node IDs for each timestamp
        if self.batch_output is None:
            raise RuntimeError("No Results Yet.")
        voltage_results = self.batch_output["voltage"]
        node_ids = self.model.get_component_ids(ComponentType.node)
        timestamps = self.p_profile.index

        max_voltage = np.max(voltage_results, axis =1)
        min_voltage= np.min(voltage_results, axis=1)

        max_indices= np.argmax(voltage_results, axis= 1)
        min_indices= np.argmin(voltage_results, axis =1)
        
        max_nodes = [node_ids[i] for i in max_indices]
        min_nodes = [node_ids[i] for i in min_indices]

        pass

    def get_line_summary(self):
        # TODO: Compute energy loss (with trapezoidal rule) and max/min loading for each line
        pass