"""
This module contains the power grid model and the processing around it in the TimeSeriesPowerFlow class.
"""

import numpy as np
import pandas as pd
from power_grid_model import (
    CalculationMethod,
    ComponentType,
    DatasetType,
    PowerGridModel,
    initialize_array,
)
from power_grid_model.utils import json_deserialize


class NoValidOutputDataError(Exception):
    """Raised when there is no output from the power_grid_model to work with."""


class LoadProfileMismatchError(Exception):
    """Raised when the active and reactive load profiles do not align."""



class TimeSeriesPowerFlow:
    """
    This class contains the processing around the the power-grid-model from the power_grid_model package.
    """

    def __init__(self, pgm_path: str, p_path: str, q_path: str):

        # Load grid
        with open(pgm_path, "r", encoding="utf-8") as file:
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
        self.voltage_summary = None
        self.line_summary = None

    def run(self):
        """
        After initializing the class and setting up the model properties, this function can be run the process the
        model and save the output to batch_output, voltage_summary and line_summary.
        """
        num_time_stamps, num_sym_loads = self.p_profile.shape

        update_sym_load = initialize_array(DatasetType.update, ComponentType.sym_load, (num_time_stamps, num_sym_loads))
        update_sym_load["id"] = [self.p_profile.columns.tolist()]
        update_sym_load["p_specified"] = self.p_profile
        update_sym_load["q_specified"] = self.q_profile

        time_series_mutation = {ComponentType.sym_load: update_sym_load}

        self.batch_output = self.model.calculate_power_flow(
            update_data=time_series_mutation,
            symmetric=True,
            error_tolerance=1e-8,
            max_iterations=20,
            calculation_method=CalculationMethod.newton_raphson,
        )

        self.voltage_summary = self._get_voltage_summary()
        self.line_summary = self._get_line_summary()

    def _get_voltage_summary(self):
        """
        This function summarizes the maximum an minimum per-unit voltages per timestamp and saves that
        value and the corresponding node to a pandas dataframe row.
        """

        nodes = self.batch_output["node"]
        output = pd.DataFrame(index=self.p_profile.index)
        output.index.name = "timestamp"

        # determine maximum and minimum voltage per line
        temp_max_node = []
        temp_max_value = []
        temp_min_node = []
        temp_min_value = []

        for timestamp in nodes:
            i_max = timestamp["u_pu"].argmax()
            temp_max_value.append(timestamp[i_max]["u_pu"])
            temp_max_node.append(timestamp[i_max]["id"])

            i_min = timestamp["u_pu"].argmin()
            temp_min_value.append(timestamp[i_min]["u_pu"])
            temp_min_node.append(timestamp[i_min]["id"])

        output["max_u_pu_node"] = temp_max_node
        output["max_u_pu"] = temp_max_value
        output["min_u_pu_node"] = temp_min_node
        output["min_u_pu"] = temp_min_value

        return output

    def _get_line_summary(self):
        """
        This function summarizes the maximum an minimum per-unit loadings per line and saves that value and
        the corresponding timestamp to a pandas dataframe row. It also integrates the total power loss per
        line over the timeframe of the power-grid-model.
        """

        lines = self.batch_output["line"]
        output = pd.DataFrame(index=lines[0]["id"])
        output.index.name = "line"

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

        for line in lines_swapped:
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
