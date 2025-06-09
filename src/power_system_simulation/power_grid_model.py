import json

import numpy as np
import pandas as pd
from power_grid_model import (
    CalculationMethod,
    CalculationType,
    ComponentAttributeFilterOptions,
    ComponentType,
    DatasetType,
    LoadGenType,
    PowerGridModel,
    attribute_dtype,
    initialize_array,
)
from power_grid_model.utils import json_deserialize, json_serialize
from power_grid_model.validation import assert_valid_batch_data, assert_valid_input_data



class NoValidOutputDataError(Exception):
    """Raised when there is no output from the power_grid_model to work with."""

class LoadProfileMismatchError(Exception):
    """Raised when the active and reactive load profiles do not align."""



class TimeSeriesPowerFlow:
    def __init__(self, pgm_path: str, p_path: str, q_path: str):

        # Load grid
        with open(pgm_path, "r") as file:
            self.grid_data = json_deserialize(file.read())

        # Load profile data
        self.p_profile = pd.read_parquet(p_path)
        self.q_profile = pd.read_parquet(q_path)

        # Validate profiles
        if not self.p_profile.index.equals(self.q_profile.index):
            raise LoadProfileMismatchError("Timestamps do not match between p and q profiles.")
        if not self.p_profile.columns.equals(self.q_profile.columns):
            raise LoadProfileMismatchError("Load IDs do not match between p and q profiles.")

        # Create model
        self.model = PowerGridModel(self.grid_data)

        # Placeholder for batch output
        self.batch_output = None

    def run(self):
        # TODO: Create update_data using initialize_array and the profiles
        # TODO: Validate batch data and run power flow calculation
        num_time_stamps, num_sym_loads = self.p_profile.shape

        self.update_sym_load = initialize_array(
            DatasetType.update, ComponentType.sym_load, (num_time_stamps, num_sym_loads)
        )
        self.update_sym_load["id"] = [self.p_profile.columns.tolist()]
        self.update_sym_load["p_specified"] = self.p_profile
        self.update_sym_load["q_specified"] = self.q_profile

        self.time_series_mutation = {ComponentType.sym_load: self.update_sym_load}

        self.batch_output = self.model.calculate_power_flow(
            update_data=self.time_series_mutation,
            symmetric=True,
            error_tolerance=1e-8,
            max_iterations=20,
            calculation_method=CalculationMethod.newton_raphson,
        )

    def get_voltage_summary(self):
        # TODO: Aggregate max/min voltage and corresponding node IDs for each timestamp
        pass

    def _get_line_summary(self):

        try:
            lines = self.batch_output['line']
        except TypeError:
            raise NoValidOutputDataError("No output data from the power-grid-model. Try running the model first using the run() function.") 
        except KeyError:
            raise NoValidOutputDataError("The output from the power-grid-model does not contain a line table. Please check the settings of the model and try re-running it.")
        except:
            raise Exception("An unknow error occurred while trying to access the output of the power-grid-model.")
        
        output = pd.DataFrame({'Line ID': lines[0]['id']})

        # calculate total power loss per line
        s_from = lines['s_from']
        s_to = lines['s_to']   
        p_loss = np.abs(s_from - s_to)

        hours_since_start = (self.p_profile.index - self.p_profile.index[0]).total_seconds() / 3600 # get the timestamps in terms of hours (float) for integration of power over time
        output['energy_loss'] = np.trapezoid(p_loss, x=hours_since_start, axis=0) / 1000 # calculate the energy loss over time using trapezoidal integratian in kWh

        return output
