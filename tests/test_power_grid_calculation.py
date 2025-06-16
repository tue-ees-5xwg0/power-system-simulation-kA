from contextlib import nullcontext as does_not_raise

import pandas as pd
import pytest
from power_grid_model import ComponentType
from test_utilities import compare_pandas_dataframes_fp

from power_system_simulation.exceptions import LoadProfileMismatchError
from power_system_simulation.power_grid_calculation import PowerGrid

# testdata filepaths
pgm_tiny_path = "tests/test_data/tiny_power_grid/input_network_data.json"
p_profile_tiny_path = "tests/test_data/tiny_power_grid/active_power_profile.parquet"
q_profile_tiny_path = "tests/test_data/tiny_power_grid/reactive_power_profile.parquet"
line_summary_tiny_path = "tests/test_data/tiny_power_grid/test_line_summary.csv"
voltage_summary_tiny_path = "tests/test_data/tiny_power_grid/test_voltage_summary.csv"

pgm_small_path = "tests/test_data/small_power_grid/input_network_data.json"
p_profile_small_path = "tests/test_data/small_power_grid/active_power_profile.parquet"
q_profile_small_path = "tests/test_data/small_power_grid/reactive_power_profile.parquet"
ev_p_profile_small_path = "tests/test_data/small_power_grid/ev_active_power_profile.parquet"
line_summary_small_path = "tests/test_data/small_power_grid/test_line_summary.csv"
voltage_summary_small_path = "tests/test_data/small_power_grid/test_voltage_summary.csv"


def test_power_grid_normal_init():
    test_grid = PowerGrid(pgm_small_path, p_profile_path=p_profile_small_path, q_profile_path=q_profile_small_path)

    assert test_grid.p_profile.shape == (960, 4)
    assert test_grid.p_profile.shape == (960, 4)


def test_power_grid_run():
    test_grid = PowerGrid(pgm_small_path, p_profile_path=p_profile_small_path, q_profile_path=q_profile_small_path)
    test_grid.run()

    # checking if there is something stored in batch_output
    assert test_grid.batch_output is not None

    # checking if the node voltages are stored in batch_output
    assert ComponentType.node in test_grid.batch_output


def test_power_grid_model_init_err_load_profile_mismatch():
    test_grid = PowerGrid(pgm_small_path)

    time_stamps1 = pd.date_range("2025-01-01", periods=3, freq="h")
    time_stamps2 = pd.date_range("2025-02-01", periods=3, freq="h")
    p_df = pd.DataFrame(
        data=[[1.0, 2.0], [1.1, 2.1], [1.2, 2.2]],
        index=time_stamps1,
        columns=[3, 5],
    )
    q_df = pd.DataFrame(
        data=[[0.5, 1.5], [0.6, 1.6], [0.7, 1.7]],
        index=time_stamps1,
        columns=[4, 5],
    )

    test_grid.p_profile = p_df
    test_grid.q_profile = q_df

    with pytest.raises(LoadProfileMismatchError, match="Load IDs do not match between p and q profiles."):
        test_grid.run()

    q_df = pd.DataFrame(
        data=[[0.5, 1.5], [0.6, 1.6], [0.7, 1.7]],
        index=time_stamps2,
        columns=[3, 5],
    )

    test_grid.q_profile = q_df

    with pytest.raises(LoadProfileMismatchError, match="Timestamps do not match between p and q profiles."):
        test_grid.run()


def test_get_voltage_summary():
    test_grid = PowerGrid(pgm_small_path, p_profile_path=p_profile_small_path, q_profile_path=q_profile_small_path)

    # test initialized to None
    assert test_grid.voltage_summary is None

    # test after running power model
    test_grid.run()
    assert test_grid.voltage_summary is not None

    # compare dataframe to a reference dataframe
    test_results = compare_pandas_dataframes_fp(
        test_grid.voltage_summary,
        pd.read_csv(voltage_summary_small_path, index_col=0, parse_dates=["timestamp"]),
        ["max_u_pu_node", "max_u_pu", "min_u_pu_node", "min_u_pu"],
    )
    assert test_results[0]


def test_power_grid_model_get_line_summary():

    test_grid = PowerGrid(pgm_small_path, p_profile_path=p_profile_small_path, q_profile_path=q_profile_small_path)

    # test initialized to None
    assert test_grid.line_summary is None

    # test after running power model
    test_grid.run()
    assert test_grid.line_summary is not None

    # compare dataframe to a reference dataframe
    test_results = compare_pandas_dataframes_fp(
        test_grid.line_summary,
        pd.read_csv(line_summary_small_path, index_col=0),
        ["max_loading_timestamp", "max_loading", "min_loading_timestamp", "min_loading"],
    )
    assert test_results[0]


def test_feature_ev_penetration_level():

    test_grid = PowerGrid(pgm_small_path, p_profile_path=p_profile_small_path, q_profile_path=q_profile_small_path)

def optimum_tap_position():

    test_grid = PowerGrid(pgm_small_path, p_profile_path=p_profile_small_path, q_profile_path=q_profile_small_path)

    

