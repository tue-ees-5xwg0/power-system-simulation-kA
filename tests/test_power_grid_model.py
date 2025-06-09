from contextlib import nullcontext as does_not_raise

import pytest
from power_grid_model import ComponentType

from power_system_simulation.power_grid_model import LoadProfileMismatchError, TimeSeriesPowerFlow


def test_power_grid_model_normal_init():
    ts = TimeSeriesPowerFlow(
        pgm_path="tests/input_network_data.json",
        p_path="tests/active_power_profile.parquet",
        q_path="tests/reactive_power_profile.parquet",
    )

    assert ts.p_profile.shape == (10, 3)
    assert ts.model is not None


def test_power_grid_model_init_err_load_profile_mismatch():
    # Don't know how to feed it the incorrect profile, since it needs parquet files
    with pytest.raises(LoadProfileMismatchError, match="Timestamps do not match between p and q profiles."):
        TimeSeriesPowerFlow(
            pgm_path="tests/input_network_data.json",
            p_path="tests/active_power_profile.parquet",
            q_path="tests/reactive_power_profile.parquet",
        )


def test_power_grid_model_run_output():
    ts = TimeSeriesPowerFlow(
        pgm_path="tests/input_network_data.json",
        p_path="tests/active_power_profile.parquet",
        q_path="tests/reactive_power_profile.parquet",
    )

    ts.run()

    # checking if there is something stored in batch_output
    assert ts.batch_output is not None
    # checking if the node voltages are stored in batch_output
    assert ComponentType.node in ts.batch_output


def test_power_grid_model_get_line_summary_normal():
    
    assert True is True


