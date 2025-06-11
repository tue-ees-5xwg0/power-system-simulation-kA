from contextlib import nullcontext as does_not_raise
import pytest
import pandas as pd

from power_system_simulation.power_grid_model import TimeSeriesPowerFlow, LoadProfileMismatchError
from power_grid_model import ComponentType

def test_power_grid_model_normal_init():
    ts = TimeSeriesPowerFlow(
        pgm_path="tests/input_network_data.json",
        p_path="tests/active_power_profile.parquet",
        q_path="tests/reactive_power_profile.parquet"
    )
    assert ts.p_profile.shape == (10, 3) 
    assert ts.model is not None

def test_power_grid_model_init_err_load_profile_mismatch():
    with pytest.raises(LoadProfileMismatchError, match="Timestamps do not match between p and q profiles."):
        TimeSeriesPowerFlow(
            pgm_path="tests/input_network_data.json",
            p_path="tests/active_power_profile.parquet",
            q_path="tests/wrong_reactive_profile.parquet"  
        )

def test_power_grid_model_run_output():
    ts = TimeSeriesPowerFlow(
        pgm_path="tests/input_network_data.json",
        p_path="tests/active_power_profile.parquet",
        q_path="tests/reactive_power_profile.parquet"
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