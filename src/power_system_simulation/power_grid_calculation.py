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

from power_system_simulation.exceptions import LoadProfileMismatchError
from power_system_simulation.graph_processing import create_graph, find_alternative_edges, find_downstream_vertices
from power_system_simulation.input_data_validation import (
    load_grid_json,
    load_meta_data_json,
    validate_ev_charging_profile,
    validate_meta_data,
    validate_power_grid_data,
    validate_power_profiles_timestamps,
)

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
        # load and validate power grid and meta-data
        self.power_grid = load_grid_json(power_grid_path)
        validate_power_grid_data(self.power_grid)
        self.meta_data = load_meta_data_json(power_grid_meta_data_path)
        validate_meta_data(self.power_grid, self.meta_data)

        # load and validate power profiles. Only validates if both power profiles are initiated together.
        if p_profile_path is not None:
            self.p_profile = pd.read_parquet(p_profile_path)
        if q_profile_path is not None:
            self.q_profile = pd.read_parquet(q_profile_path)

        if p_profile_path is not None and q_profile_path is not None:
            self._validate_power_profiles_load_ids()
            validate_power_profiles_timestamps(self.p_profile, self.q_profile)

        # create and validate graph (validation happens in the graph)
        self.update_graph()

        # initialize power-grid-model output
        self.voltage_summary = None
        self.line_summary = None

    def update_graph(self):
        """
        Used to update the internal graph after changing the power_grid data.
        """
        self.graph = create_graph(self.power_grid)

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

        batch_output = model.calculate_power_flow(
            update_data=time_series_mutation,
            symmetric=True,
            error_tolerance=1e-8,
            max_iterations=20,
            calculation_method=CalculationMethod.newton_raphson,
        )

        del model
        self.voltage_summary = self._get_voltage_summary(batch_output)
        self.line_summary = self._get_line_summary(batch_output)
        del batch_output

    def _validate_power_profiles_load_ids(self):
        # check for matching load ids between profiles
        if not self.p_profile.columns.equals(self.q_profile.columns):
            raise LoadProfileMismatchError("Load IDs do not match between power profiles.")

        # check for presense of load ids in the power_grid
        for profile_id in self.p_profile.columns:
            found = False
            for load in self.power_grid["sym_load"]:
                if load["id"] == profile_id:
                    found = True
            if not found:
                raise LoadProfileMismatchError(f"Load ID {profile_id} of in power_profiles not found in sym_loads.")

    def _get_voltage_summary(self, batch_output):
        """
        This function summarizes the maximum an minimum per-unit voltages per timestamp and saves that
        value and the corresponding node to a pandas dataframe row.
        """

        nodes = batch_output["node"]
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

        # summarize output into dataframe
        output["max_u_pu_node"] = temp_max_node
        output["max_u_pu"] = temp_max_value
        output["min_u_pu_node"] = temp_min_node
        output["min_u_pu"] = temp_min_value

        return output

    def _get_line_summary(self, batch_output):
        """
        This function summarizes the maximum an minimum per-unit loadings per line and saves that value and
        the corresponding timestamp to a pandas dataframe row. It also integrates the total power loss per
        line over the timeframe of the power-grid-model.
        """

        lines = batch_output["line"]
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

        # summarize output into dataframe
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
    # power_grid.run()

    power_grid_copy = copy.deepcopy(power_grid)
    rndm = random.Random(seed)

    # Load and validate EV profile
    ev_profiles = pd.read_parquet(ev_charging_profile_path)
    validate_ev_charging_profile(power_grid_copy, ev_profiles)
    validate_power_profiles_timestamps(power_grid_copy.p_profile, ev_profiles)

    # Get grid data
    sym_load_ids = power_grid_copy.p_profile.columns.tolist()
    num_houses = len(sym_load_ids)
    lv_feeder_ids = power_grid_copy.meta_data["lv_feeders"]
    num_feeders = len(lv_feeder_ids)
    num_EV_per_LV = math.floor(penetration_level * num_houses / num_feeders)

    # Map feeders to downstream houses
    map_feeder_house = {}
    for feeder_id in lv_feeder_ids:
        downstream_vertices = find_downstream_vertices(power_grid_copy.graph, feeder_id, False)
        feeder_houses = [node for node in downstream_vertices if node in sym_load_ids]
        map_feeder_house[feeder_id] = feeder_houses

    # Assign EV profiles to houses
    for feeder_id, feeder_houses in map_feeder_house.items():
        if num_EV_per_LV > len(feeder_houses):
            raise ValueError(f"Feeder {feeder_id} doesn't not have enough houses.")

        selected_houses = rndm.sample(feeder_houses, num_EV_per_LV)
        selected_ev_profiles = rndm.sample(list(ev_profiles.columns), num_EV_per_LV)

        for house_id, ev_profile_id in zip(selected_houses, selected_ev_profiles):
            ev_profile = ev_profiles[ev_profile_id]
            power_grid_copy.p_profile[house_id] += ev_profile
            ev_profiles.drop(columns=[ev_profile_id], inplace=True)

    # run model with ev_profile added to the load and return output
    power_grid_copy.run()
    return [power_grid_copy.voltage_summary, power_grid_copy.line_summary]


def optimum_tap_position(power_grid: PowerGrid, optimization_criterium: optimization_criteria):
    """
    returns optimal tap position of the transfomer by repeating time-series power flow calculation
    it does this for: The minimal total energy loss of all the lines and the whole time period.
    and The minimal (averaged across all nodes) deviation of (max and min) p.u. node voltages with respect to 1 p.u.
    """
    # pg_copy = copy.deepcopy(power_grid)
    options = get_args(optimization_criteria)
    assert optimization_criterium in options, f"'{optimization_criterium}' is not in {options}"

    min_tp = power_grid.power_grid["transformer"][0]["tap_min"]
    max_tp = power_grid.power_grid["transformer"][0]["tap_max"]
    tap_range = range(max_tp, min_tp + 1)

    # lower is better
    best_score = float("inf")
    best_tap = -1

    for tap_pos in tap_range:
        pg_copy = copy.deepcopy(power_grid)
        pg_copy.power_grid["transformer"][0]["tap_pos"] = tap_pos
        pg_copy.run()

        score = float("inf")

        if optimization_criterium == "minimal_energy_loss":
            total_energy_loss = pg_copy.line_summary["energy_loss"].sum()
            score = total_energy_loss

        elif optimization_criterium == "minimal_deviation_u_pu":
            voltage_dev = abs(pg_copy.voltage_summary["max_u_pu"] - 1.0) + abs(
                pg_copy.voltage_summary["min_u_pu"] - 1.0
            )

            score = voltage_dev.mean()

        print(score)

        if score < best_score:
            best_score = score
            best_tap = tap_pos
        del pg_copy

    return best_tap


def n_1_calculation(power_grid: PowerGrid, line_id: int):
    """
    This function returns an overview of possible alternative lines when a provided line is disabled. This overview
    includes the maximum line loading and timestampt per alternative line.
    """

    # initialize output
    output = pd.DataFrame(columns=["maximum_line_loading_id", "maximum_line_loading_timestamp", "maximum_line_loading"])
    output.index.name = "alternative_line"

    grid = power_grid.line_summary
    index = grid["max_loading"].idxmax()
    output.loc[line_id] = {
        "maximum_line_loading_id": index,
        "maximum_line_loading_timestamp": grid.loc[index, "max_loading_timestamp"],
        "maximum_line_loading": grid.loc[index, "max_loading"],
    }

    # check for alternative lines
    # power_grid.update_graph()
    alternative_lines = find_alternative_edges(power_grid.graph, line_id)
    print(alternative_lines)

    # run model for each alternative line
    for alternative_line in alternative_lines:
        power_grid_copy = copy.deepcopy(power_grid)

        # turn provided line off and turn alternative on
        index = power_grid_copy.power_grid["line"]["id"] == alternative_line
        power_grid_copy.power_grid["line"]["from_status"][index] = 1
        power_grid_copy.power_grid["line"]["to_status"][index] = 1

        index = power_grid_copy.power_grid["line"]["id"] == line_id
        power_grid_copy.power_grid["line"]["from_status"][index] = 0
        power_grid_copy.power_grid["line"]["to_status"][index] = 0

        # run model
        power_grid_copy.run()

        # summarize outputs into dataframe
        summary = power_grid_copy.line_summary
        index = summary["max_loading"].idxmax()
        output.loc[alternative_line] = {
            "maximum_line_loading_id": index,
            "maximum_line_loading_timestamp": summary.loc[index, "max_loading_timestamp"],
            "maximum_line_loading": summary.loc[index, "max_loading"],
        }

        del power_grid_copy

    return output
