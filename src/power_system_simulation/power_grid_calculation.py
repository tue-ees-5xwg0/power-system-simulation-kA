"""
This module contains the power grid class and the processing around it.
"""

import copy
from typing import Literal, get_args

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

from power_system_simulation.exceptions import (
    DataNotFoundError,
    LoadProfileMismatchError,
    NoValidOutputDataError,
    ValidationError,
)
from power_system_simulation.graph_processing import *

_OPTIMIZATION_CRITERIA = Literal["minimal_deviation_u_pu", "minimal_energy_loss"]


class PowerGrid:
    """
    This class functions as a powergrid with a power_grid_model and power_grid_graph build into it for integrated
    power-flow calculations and graph processing.
    """

    def __init__(self, power_grid_path: str, *, p_profile_path: str = None, q_profile_path: str = None):

        self.power_grid = None
        self.load_grid_json(power_grid_path)
        self.graph = None

        self.p_profile = None
        self.q_profile = None

        if p_profile_path is not None:
            self.load_p_profile_parquet(p_profile_path)

        if q_profile_path is not None:
            self.load_q_profile_parquet(q_profile_path)

        self.batch_output = None
        self.voltage_summary = None
        self.line_summary = None

    def load_grid_json(self, path):
        with open(path, "r", encoding="utf-8") as file:
            self.power_grid = json_deserialize(file.read())

    def load_p_profile_parquet(self, path):
        self.p_profile = pd.read_parquet(path)

    def load_q_profile_parquet(self, path):
        self.q_profile = pd.read_parquet(path)

    def make_graph(self):
        self.graph = create_graph(self.power_grid)

    def run(self):
        """
        After initializing the class and setting up the model properties, this function can be run to process the
        model and save the output to batch_output, voltage_summary and line_summary.
        """
        self._validate_power_profiles()
        model = PowerGridModel(self.power_grid)
        num_time_stamps, num_sym_loads = self.p_profile.shape

        update_sym_load = initialize_array(DatasetType.update, ComponentType.sym_load, (num_time_stamps, num_sym_loads))
        update_sym_load["id"] = [self.p_profile.columns.tolist()]
        update_sym_load["p_specified"] = self.p_profile
        update_sym_load["q_specified"] = self.q_profile

        time_series_mutation = {ComponentType.sym_load: update_sym_load}

        self.batch_output = model.calculate_power_flow(
            update_data=time_series_mutation,
            symmetric=True,
            error_tolerance=1e-8,
            max_iterations=20,
            calculation_method=CalculationMethod.newton_raphson,
        )

        self.voltage_summary = self._get_voltage_summary()
        self.line_summary = self._get_line_summary()

    def _validate_power_profiles(self):
        # if self.p_profile is None:
        #     raise ValidationError(
        #         "No data found in the p_profile. Make sure an active power profile is loaded into the object."
        #     )
        # if self.q_profile is None:
        #     raise ValidationError(
        #         "No data found in the q_profile. Make sure an reactive power profile is loaded into the object."
        #     )

        # if not self.p_profile.index.equals(self.q_profile.index):
        #     raise LoadProfileMismatchError("Timestamps do not match between p and q profiles.")
        # if not self.p_profile.columns.equals(self.q_profile.columns):
        #     raise LoadProfileMismatchError("Load IDs do not match between p and q profiles.")
        pass

    def _validate_power_grid(self):
        try:
            assert self.power_grid is not None
        except:
            raise ValueError("power_grid not found, please make a power grid first.")
        pass

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


def ev_penetration_level(power_grid: PowerGrid, ev_charging_profile_path: str, penetration_level: float):
    
    pg_copy = copy.deepcopy(power_grid)
    
    # TODO do something with the pg to randomly distribute ev chargers from the ev

    return [pg_copy.voltage_summary, pg_copy.line_summary]


# def optimum_tap_position(
#     power_grid: PowerGrid, optimization_criterium: _OPTIMIZATION_CRITERIA = "minimal_deviation_u_pu"
# ):
#     pg_copy = copy.deepcopy(power_grid)
#     options = get_args(_OPTIMIZATION_CRITERIA)
#     assert optimization_criterium in options, f"'{optimization_criterium}' is not in {options}"

#     # TODO do something with the pg like iterate with different tap positions and return the optimum tap position for the transformer.

#     return optimum_tap_position


# def n_1_calculation(power_grid: PowerGrid):
#     pg_copy = copy.deepcopy(power_grid)
#     output = pd.DataFrame()

#     # TODO create alternative power_grids, one for each different alternative line. Summarize the results into the output table. Use
#     # the graph_processor to find out which lines to use.

#     return output
