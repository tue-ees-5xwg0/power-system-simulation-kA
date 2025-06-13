from contextlib import nullcontext as does_not_raise

import pandas as pd
import pytest
from power_grid_model import ComponentType

from power_system_simulation.power_grid_model import LoadProfileMismatchError, TimeSeriesPowerFlow


def test_power_grid_model_load_grid_and_data_and_create_model():
    ts = TimeSeriesPowerFlow()
    ts.load_data(
        pgm_path="tests/input_network_data.json",
        p_path="tests/active_power_profile.parquet",
        q_path="tests/reactive_power_profile.parquet",
    )
    ts.create_model()

    assert ts.p_profile.shape == (10, 3)
    assert ts.model is not None


def test_power_grid_model_init_err_load_profile_mismatch():
    ts = TimeSeriesPowerFlow()
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

    ts.load_data(
        pgm_path="tests/input_network_data.json",
        p_df=p_df,
        q_df=q_df,
    )

    with pytest.raises(LoadProfileMismatchError, match="Load IDs do not match between p and q profiles."):
        ts.create_model()

    q_df = pd.DataFrame(
        data=[[0.5, 1.5], [0.6, 1.6], [0.7, 1.7]],
        index=time_stamps2,
        columns=[3, 5],
    )

    ts.load_data(
        pgm_path="tests/input_network_data.json",
        p_df=p_df,
        q_df=q_df,
    )

    with pytest.raises(LoadProfileMismatchError, match="Timestamps do not match between p and q profiles."):
        ts.create_model()


def test_power_grid_model_run_output():
    ts = TimeSeriesPowerFlow()
    ts.load_data(
        pgm_path="tests/input_network_data.json",
        p_path="tests/active_power_profile.parquet",
        q_path="tests/reactive_power_profile.parquet",
    )
    ts.create_model()
    ts.run()

    # checking if there is something stored in batch_output
    assert ts.batch_output is not None
    # checking if the node voltages are stored in batch_output
    assert ComponentType.node in ts.batch_output
