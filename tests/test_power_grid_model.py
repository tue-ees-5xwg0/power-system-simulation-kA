from contextlib import nullcontext as does_not_raise

import pandas as pd
import pytest
from power_grid_model import ComponentType
from test_utilities import compare_pandas_dataframes_fp

from power_system_simulation.power_grid_model import LoadProfileMismatchError, TimeSeriesPowerFlow

# testdata filepaths
pgm_small_path = "tests/test_power_grid_model_data/input_network_data.json"
p_profile_small_path = "tests/test_power_grid_model_data/active_power_profile.parquet"
q_profile_small_path = "tests/test_power_grid_model_data/reactive_power_profile.parquet"
line_summary_small_path = "tests/test_power_grid_model_data/test_line_summary.csv"


def test_power_grid_model_normal_init():
    ts = TimeSeriesPowerFlow(
        pgm_path=pgm_small_path,
        p_path=p_profile_small_path,
        q_path=q_profile_small_path,
    )

    assert ts.p_profile.shape == (10, 3)
    assert ts.model is not None


def test_power_grid_model_init_err_load_profile_mismatch():
    with pytest.raises(LoadProfileMismatchError, match="Timestamps do not match between p and q profiles."):
        TimeSeriesPowerFlow(
            pgm_path=pgm_small_path,
            p_path=p_profile_small_path,
            q_path=q_profile_small_path,
        )


def test_power_grid_model_run_output():
    ts = TimeSeriesPowerFlow(
        pgm_path=pgm_small_path,
        p_path=p_profile_small_path,
        q_path=q_profile_small_path,
    )
    ts.run()
    assert ts.batch_output is not None
    assert ComponentType.node in ts.batch_output

def test_get_voltage_summary():
    ts = TimeSeriesPowerFlow(
        pgm_path="tests/input_network_data.json",
        p_path="tests/active_power_profile.parquet",
        q_path="tests/reactive_power_profile.parquet"
    )
    ts.run()
    summary = ts.get_voltage_summary()

  
    assert isinstance(summary, pd.DataFrame)
    assert summary.shape[0] == ts.p_profile.shape[0]  
    expected_cols = {"max_voltage_pu", "max_voltage_node", "min_voltage_pu", "min_voltage_node"}
    assert expected_cols.issubset(summary.columns)

    assert summary["max_voltage_pu"].between(0.9, 1.1).all()
    assert summary["min_voltage_pu"].between(0.8, 1.1).all()

    assert summary["max_voltage_node"].notna().all()
    assert summary["min_voltage_node"].notna().all()
    assert summary["max_voltage_node"].apply(lambda x: isinstance(x, str)).all()
    assert summary["min_voltage_node"].apply(lambda x: isinstance(x, str)).all()
    # checking if there is something stored in batch_output
    assert ts.batch_output is not None
    # checking if the node voltages are stored in batch_output
    assert ComponentType.node in ts.batch_output


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
    test_results = compare_pandas_dataframes_fp(ts.line_summary, pd.read_csv(line_summary_small_path, index_col=0), ['max_loading', 'min_loading'])
    assert test_results[0]
