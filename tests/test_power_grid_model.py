from contextlib import nullcontext as does_not_raise

import pandas as pd
import pytest
from power_grid_model import ComponentType
from test_utilities import compare_pandas_dataframes_fp

from power_system_simulation.power_grid_model import (
    LoadProfileMismatchError,
    PowerGrid,
    PowerGridProcessor,
    PowerProfile,
)

# testdata filepaths
pgm_small_path = "tests/test_power_grid_model_data/input_network_data.json"
p_profile_small_path = "tests/test_power_grid_model_data/active_power_profile.parquet"
q_profile_small_path = "tests/test_power_grid_model_data/reactive_power_profile.parquet"
line_summary_small_path = "tests/test_power_grid_model_data/test_line_summary.csv"
voltage_summary_small_path = "tests/test_power_grid_model_data/test_voltage_summary.csv"


def test_power_grid_model_normal_init():
    ts = TimeSeriesPowerFlow(
        pgm_path=pgm_small_path,
        p_path=p_profile_small_path,
        q_path=q_profile_small_path,
    )

    assert ts.p_profile.shape == (10, 3)
    assert ts.p_profile.shape == (10, 3)
    assert ts.model is not None


def test_power_grid_model_run_output():
    ts = TimeSeriesPowerFlow(
        pgm_path=pgm_small_path,
        p_path=p_profile_small_path,
        q_path=q_profile_small_path,
    )
    ts.run()

    # checking if there is something stored in batch_output
    assert ts.batch_output is not None
    assert ts.batch_output is not None
    # checking if the node voltages are stored in batch_output
    assert ComponentType.node in ts.batch_output


def test_get_voltage_summary():
    ts = TimeSeriesPowerFlow(
        pgm_path=pgm_small_path,
        p_path=p_profile_small_path,
        q_path=q_profile_small_path,
    )

    # test initialized to None
    assert ts.voltage_summary is None

    # test after running power model
    ts.run()
    assert ts.voltage_summary is not None

    # compare dataframe to a reference dataframe
    test_results = compare_pandas_dataframes_fp(
        ts.voltage_summary,
        pd.read_csv(voltage_summary_small_path, index_col=0, parse_dates=["timestamp"]),
        ["max_u_pu_node", "max_u_pu", "min_u_pu_node", "min_u_pu"],
    )
    assert test_results[0]


def test_power_grid_model_get_line_summary():

    ts = TimeSeriesPowerFlow(
        pgm_path=pgm_small_path,
        p_path=p_profile_small_path,
        q_path=q_profile_small_path,
    )

    # test initialized to None
    assert ts.line_summary is None

    # test after running power model
    ts.run()
    assert ts.line_summary is not None

    # compare dataframe to a reference dataframe
    test_results = compare_pandas_dataframes_fp(
        ts.line_summary,
        pd.read_csv(line_summary_small_path, index_col=0),
        ["max_loading_timestamp", "max_loading", "min_loading_timestamp", "min_loading"],
    )
    assert test_results[0]
