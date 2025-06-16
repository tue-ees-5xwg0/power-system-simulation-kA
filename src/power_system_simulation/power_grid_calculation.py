"""
This module contains the power grid class and the processing around it.
"""

import copy
import math
import random
from typing import Literal, Optional, get_args

import numpy as np
import pandas as pd
from power_grid_model import (
    CalculationMethod,
    ComponentType,
    DatasetType,
    PowerGridModel,
    initialize_array,
)

from power_system_simulation.input_data_validation import (
    load_grid_json,
    load_meta_data_json,
    validate_ev_charging_profile,
    validate_meta_data,
    validate_power_grid_data,
    validate_power_profiles_timestamps,
)
from power_system_simulation.exceptions import LoadProfileMismatchError, ValidationError
from power_system_simulation.graph_processing import create_graph, find_downstream_vertices, find_lv_feeder_ids

optimization_criteria = Literal["minimal_deviation_u_pu", "minimal_energy_loss"]


class PowerGrid:
    """
    This class functions as a powergrid with a power_grid_model and power_grid_graph build into it for integrated
    power-flow calculations and graph processing.
    """

    def __init__(
        self,
        power_grid_path: str,
        power_grid_meta_data_path: str,
        p_profile_path: Optional[str] = None,
        q_profile_path: Optional[str] = None,
    ):

        self.power_grid = load_grid_json(power_grid_path)
        validate_power_grid_data(self.power_grid)
        self.meta_data = load_meta_data_json(power_grid_meta_data_path)
        validate_meta_data(self.power_grid, self.meta_data)
        self.graph = create_graph(self.power_grid)

        self.p_profile = None
        self.q_profile = None

        if p_profile_path is not None:
            self.p_profile = pd.read_parquet(p_profile_path)

        if q_profile_path is not None:
            self.q_profile = pd.read_parquet(q_profile_path)

        if p_profile_path is not None and q_profile_path is not None:
            self._validate_power_profiles_load_ids()
            validate_power_profiles_timestamps(self.p_profile, self.q_profile)

        self.batch_output = None
        self.voltage_summary = None
        self.line_summary = None

    def load_p_profile_parquet(self, path):
        """
        Loads the p_profile into the PowerGrid object.
        """
        self.p_profile = pd.read_parquet(path)

    def load_q_profile_parquet(self, path):
        """
        Loads the q_profile into the PowerGrid object.
        """
        self.q_profile = pd.read_parquet(path)

    def update_graph(self):
        """
        Used to update the internal graph after changing the power_grid data.
        """
        create_graph(self.power_grid)

    def run(self):
        """
        After initializing the class and setting up the model properties, this function can be run to process the
        model and save the output to batch_output, voltage_summary and line_summary.
        """
        self._validate_power_profiles_load_ids()
        validate_power_profiles_timestamps(self.p_profile, self.q_profile)

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

    def _validate_power_profiles_load_ids(self):
        if not self.p_profile.columns.equals(self.q_profile.columns):
            raise LoadProfileMismatchError("Load IDs do not match between power profiles.")

        for profile_id in self.p_profile.columns:
            found = False
            for load in self.power_grid["sym_load"]:
                if load["id"] == profile_id:
                    found = True
            if not found:
                raise LoadProfileMismatchError(f"Load ID {profile_id} of in power_profiles not found in sym_loads.")

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


def ev_penetration_level(
    power_grid: PowerGrid, ev_charging_profile_path: str, penetration_level: float, seed: Optional[int] = None
):
    """
    This function randomly adds EV charging pofiles to a a percentage of household (sym_loads) based on
    a penetration level. Then it runs a time-series powerflow and returns the voltage and line summaries.
    """
    pg_copy = copy.deepcopy(power_grid)
    rndm = random.Random(seed)

    # Load EV profiles
    ev_profiles = pd.read_parquet(ev_charging_profile_path)
    available_ev_profiles = ev_profiles.copy()
    ev_p_profile = pg_copy.p_profile.copy()
    ev_charging_profile = pd.read_parquet(ev_charging_profile_path)

    # Get grid data
    sym_load_ids = pg_copy.p_profile.columns.tolist()
    num_houses = len(sym_load_ids)
    pg_copy_graph = create_graph(pg_copy)
    lv_feeder_ids = find_lv_feeder_ids(pg_copy_graph)
    num_feeders = len(lv_feeder_ids)
    num_EV_per_LV = math.floor(penetration_level * num_houses / num_feeders)
    validate_ev_charging_profile(power_grid, ev_charging_profile)
    validate_power_profiles_timestamps(power_grid.p_profile, ev_charging_profile)

    # Map feeders to downstream houses
    map_feeder_house = {}
    for feeder_id in lv_feeder_ids:
        downstream_vertices = find_downstream_vertices(pg_copy_graph, feeder_id)
        feeder_houses = [node for node in downstream_vertices if node in sym_load_ids]
        map_feeder_house[feeder_id] = feeder_houses

    # Assign EV profiles to houses
    for feeder_id, feeder_houses in map_feeder_house.items():
        if num_EV_per_LV > len(feeder_houses):
            raise ValueError(f"Feeder {feeder_id} doesn not have enough houses.")

        selected_houses = rndm.sample(feeder_houses, num_EV_per_LV)
        selected_ev_profiles = rndm.sample(list(available_ev_profiles.columns), num_EV_per_LV)

        for house_id, ev_profile_id in zip(selected_houses, selected_ev_profiles):
            ev_profile = available_ev_profiles[ev_profile_id]
            ev_p_profile[house_id] += ev_profile
            available_ev_profiles.drop(columns=[ev_profile_id], inplace=True)

    # Run powerflow with altered p_profile
    pg_copy.p_profile = ev_p_profile
    pg_copy.run()

    return [pg_copy.voltage_summary, pg_copy.line_summary]


def optimum_tap_position(power_grid: PowerGrid, optimization_criterium: optimization_criteria):
    pg_copy = copy.deepcopy(power_grid)
    options = get_args(optimization_criteria)
    assert optimization_criterium in options, f"'{optimization_criterium}' is not in {options}"

    transformers = pg_copy.power_grid["transformer"]

    # TODO: move this validation to the data input stage of the PowerGrid object
    if len(transformers) != 1:
        raise ValidationError("The LV grid must contain exactly one transformer.")

    transformer_id = transformers[0]["id"]
    original_tap = transformers[0].get("tap_pos", 0)

    # TODO: extract this data from the transformer entry in the PowerGrid.power_grid data
    tap_range = range(-5, 6)

    best_score = float("inf")
    best_tap = original_tap

    for tap_pos in tap_range:

        for transformer in pg_copy.power_grid["transformer"]:
            transformer["tap_pos"] = tap_pos

        try:
            pg_copy.run()
        except Exception:
            continue  # Skip invalid tap positions

        if optimization_criterium == "minimal_energy_loss":
            total_energy_loss = pg_copy.line_summary["energy_loss"].sum()
            score = total_energy_loss

        elif optimization_criterium == "minimal_deviation_u_pu":
            voltage_dev = abs(pg_copy.voltage_summary["max_u_pu"] - 1.0) + abs(
                pg_copy.voltage_summary["min_u_pu"] - 1.0
            )
            score = voltage_dev.mean()

        if score < best_score:
            best_score = score
            best_tap = tap_pos

    return best_tap


def n_1_calculation(power_grid: PowerGrid):
    # pg_copy = copy.deepcopy(power_grid)
    # output = pd.DataFrame()

    # # TODO create alternative power_grids, one for each different alternative line. Summarize the
    # # results into the output table. Use
    # # the graph_processor to find out which lines to use.

    # return output
    pass
