import json
from typing import Optional

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


class LoadProfileMismatchError(Exception):
    """Raised when the active and reactive load profiles do not align."""


class TimeSeriesPowerFlow:
    def __init__(self):
        self.grid_data = None
        self.q_profile = None
        self.p_profile = None
        self.model = None
        self.batch_output = None

    def load_data(
        self,
        pgm_path: str,
        p_path: Optional[str] = None,
        q_path: Optional[str] = None,
        p_df: Optional[pd.DataFrame] = None,
        q_df: Optional[pd.DataFrame] = None,
    ):
        with open(pgm_path, "r") as file:
            self.grid_data = json_deserialize(file.read())

        if p_df is not None and q_df is not None:
            self.p_profile = p_df
            self.q_profile = q_df
        elif p_path is not None and q_path is not None:
            self.p_profile = pd.read_parquet(p_path)
            self.q_profile = pd.read_parquet(q_path)
        else:
            raise ValueError("Either (p_path and q_path) or (p_df and q_df) must be provided")

    def create_model(self):
        if not self.p_profile.index.equals(self.q_profile.index):
            raise LoadProfileMismatchError("Timestamps do not match between p and q profiles.")
        if not self.p_profile.columns.equals(self.q_profile.columns):
            raise LoadProfileMismatchError("Load IDs do not match between p and q profiles.")
        self.model = PowerGridModel(self.grid_data)

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

    def get_line_summary(self):
        # TODO: Compute energy loss (with trapezoidal rule) and max/min loading for each line
        pass
