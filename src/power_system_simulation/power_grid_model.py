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


class ValidationError(Exception):
    """Raised when invalid data is attempted to be used."""


class PowerGrid:
    """
    This class stores a power grid graph, this can then be used to create a PowerGridProcessor or a GraphProcessor.
    """

    def __init__(self, path=None):
        self.valid = False
        self.data = None

        if path is not None:
            self.load_json(path)

    def load_json(self, path):
        with open(path, "r", encoding="utf-8") as file:
            self.data = json_deserialize(file.read())

        self.valid = self._validate()

    def _validate(self):
        # TODO: implement validation checks
        return True

    def add_node(self):
        pass

    def remove_node(self):
        pass

    def add_line(self):
        pass

    def remove_line(self):
        pass

    def add_sym_load(self):
        pass

    def remove_sym_load(self):
        pass

    def set_source(self):
        pass


class PowerProfile:
    """
    This class stores the power profile and can be used by the PowerGridProcessor to run the model over a PowerGrid.
    """

    def __init__(self, path=None):
        self.valid = False
        self.data = None

        if path is not None:
            self.load_parquet(path)

    def load_parquet(self, path):
        self.data = pd.read_parquet(path)

        self.valid = self._validate()

    def _validate(self):
        # TODO: implement validation checks
        return True

    def add(self):
        pass

    def remove(self):
        pass


class PowerGridProcessor:
    """
    This class contains the processing around the power_grid_model from the power_grid_model package.
    """

    def __init__(self, *, power_grid_path: str = None, p_profile_path: str = None, q_profile_path: str = None):
        self.power_grid = None
        self.p_profile = None
        self.q_profile = None

        if power_grid_path is not None:
            self.power_grid = PowerGrid(power_grid_path)

        if p_profile_path is not None:
            self.p_profile = PowerProfile(p_profile_path)

        if q_profile_path is not None:
            self.q_profile = PowerProfile(q_profile_path)

        self.model = None
        self.batch_output = None
        self.voltage_summary = None
        self.line_summary = None

    def _validate_power_profiles(self):
        _validate_p_profile()
        _validate_q_profile()

        if not self.p_profile.index.equals(self.q_profile.index):
            raise LoadProfileMismatchError("Timestamps do not match between p and q profiles.")
        if not self.p_profile.columns.equals(self.q_profile.columns):
            raise LoadProfileMismatchError("Load IDs do not match between p and q profiles.")

        return True

    def _validate_power_grid(self):
        try:
            assert self.power_grid.valid
        except AssertionError:
            raise ValidationError("power_grid is not in a valid state, please update it.")
        except:
            raise ValueError("power_grid not found, please make a power grid first.")

    def _validate_p_profile(self):
        try:
            assert self.p_profile.valid
        except AssertionError:
            raise ValidationError("p_profile is not in a valid state, please update it.")
        except:
            raise ValueError("p_profile not found, please make a p_profile first.")

    def _validate_q_profile(self):
        try:
            assert self.q_profile.valid
        except AssertionError:
            raise ValidationError("q_profile is not in a valid state, please update it.")
        except:
            raise ValueError("q_profile not found, please make a p_profile first.")

    def update(self):
        """
        Updates the power_grid_model with the current power grid.
        """
        _validate_power_grid()
        self.model = PowerGridModel(self.power_grid.data)

    def run(self):
        """
        After initializing the class and setting up the model properties, this function can be run to process the
        model and save the output to batch_output, voltage_summary and line_summary.
        """
        _validate_power_profiles()

        num_time_stamps, num_sym_loads = self.p_profile.data.shape

        update_sym_load = initialize_array(DatasetType.update, ComponentType.sym_load, (num_time_stamps, num_sym_loads))
        update_sym_load["id"] = [self.p_profile.data.columns.tolist()]
        update_sym_load["p_specified"] = self.p_profile.data
        update_sym_load["q_specified"] = self.q_profile.data

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
