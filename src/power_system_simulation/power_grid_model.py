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

        # Placeholder for batch output and summaries
        self.batch_output = None
        self.line_summary = None

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

        self.line_summary = self._get_line_summary()

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

        together_df = pd.DataFrame({"max_voltage_pu": max_voltage, "max_voltage_node": max_nodes, "min_voltage_pu": min_voltage, "min_voltage_node": min_nodes}, index=timestamps)

        return together_df

    def _get_line_summary(self):

        lines = self.batch_output["line"]
        output = pd.DataFrame(index=lines[0]["id"])

        # calculate total power loss per line
        s_from = lines["s_from"]
        s_to = lines["s_to"]
        p_loss = np.abs(s_from - s_to)

        hours_since_start = (
            self.p_profile.index - self.p_profile.index[0]
        ).total_seconds() / 3600  # get the timestamps in terms of hours (float) for integration of power over time
        output["energy_loss"] = (
            np.trapezoid(p_loss, x=hours_since_start, axis=0) / 1000
        )  # calculate the energy loss over time using trapezoidal integratian in kWh

        # determine maximum and minimum loading per line
        lines_swapped = lines.swapaxes(0, 1)
        temp_max_timestamp = []
        temp_max_value = []
        temp_min_timestamp = []
        temp_min_value = []

        for i, line in enumerate(lines_swapped):
            i_max = line["loading"].argmax()
            temp_max_value.append(line[i_max]["loading"])
            temp_max_timestamp.append(self.p_profile.index[i_max])

            i_min = line["loading"].argmin()
            temp_min_value.append(line[i_min]["loading"])
            temp_min_timestamp.append(self.p_profile.index[i_min])

        output["max_loading_timestamp"] = temp_max_timestamp
        output["max_loading"] = temp_max_value
        output["min_loading_timestamp"] = temp_min_timestamp
        output["min_loading"] = temp_min_value

        return output
