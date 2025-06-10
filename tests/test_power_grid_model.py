from contextlib import nullcontext as does_not_raise

import pytest
from power_grid_model import ComponentType

from power_system_simulation.power_grid_model import LoadProfileMismatchError, TimeSeriesPowerFlow
import pandas as pd

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
    # Don't know how to feed it the incorrect profile, since it needs parquet files
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

    


