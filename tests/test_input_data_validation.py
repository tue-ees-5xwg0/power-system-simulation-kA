from contextlib import nullcontext as does_not_raise

import pytest

from power_system_simulation.exceptions import *
from power_system_simulation.input_data_validation import *
from power_system_simulation.power_grid_calculation import PowerGrid

base_test_data_path = "tests/test_data/incorrect_power_grids/"

pgm_small_path = "tests/test_data/small_power_grid/input_network_data.json"
meta_data_small_path = "tests/test_data/small_power_grid/meta_data.json"
p_profile_small_path = "tests/test_data/small_power_grid/active_power_profile.parquet"
q_profile_small_path = "tests/test_data/small_power_grid/reactive_power_profile.parquet"
ev_p_profile_small_path = "tests/test_data/small_power_grid/ev_active_power_profile.parquet"
line_summary_small_path = "tests/test_data/small_power_grid/test_line_summary.csv"
voltage_summary_small_path = "tests/test_data/small_power_grid/test_voltage_summary.csv"


def test_init_duplicate_node_ids():
    """
    Duplicate node id 4, should raise an IDNotUniqueError.

    1--<9>--2--[10]-3------(16)
    ^       |
    20     [4]
            |
            4--[12]-4------(17)
            |
           [13]
            |
            6--[14]-7--[15]-8-----(19)
                    |
                   (18)
    """

    with pytest.raises(IDNotUniqueError) as output:
        validate_power_grid_data(load_grid_json(base_test_data_path + "err_duplicate_items" + ".json"))
    assert output.value.args[0] == "There are components with duplicate IDs."


def test_init_invalid_sym_load_node_id():
    """
    A sym_load is connected to a non-existent node.

    1--<9>--2--[7]-3        99------(16)
    ^       |
    20     [11]
            |
            4--[12]-5------(17)
            |
           [13]
            |
            6--[14]-7--[15]-8-----(19)
                    |
                   (18)
    """

    with pytest.raises(IDNotFoundError) as output:
        validate_power_grid_data(load_grid_json(base_test_data_path + "err_sym_load_node_invalid" + ".json"))
    assert output.value.args[0] == "Sym_load(s) contain(s) non-existent node ID."


def test_init_invalid_line_node_id():
    """
    A line is connected to a non-existent node.

    1--<9>--2--[10]-3------(16)
    ^       |
    20     [11]   /--99
            |    /
            4--[12]  5------(17)
            |
           [13]
            |
            6--[14]-7--[15]-8-----(19)
                    |
                   (18)
    """

    with pytest.raises(IDNotFoundError) as output:
        validate_power_grid_data(load_grid_json(base_test_data_path + "err_line_node_invalid" + ".json"))
    assert output.value.args[0] == "Line(s) contain(s) non-existent node ID."


def test_init_invalid_source_node_id():
    """
    The source ID is invalid.

    1--<9>--2--[10]-3------(16)     99
            |                       ^
           [11]                     20
            |
            4--[12]-5------(17)
            |
           [13]
            |
            6--[14]-7--[15]-8-----(19)
                    |
                   (18)
    """

    with pytest.raises(IDNotFoundError) as output:
        validate_power_grid_data(load_grid_json(base_test_data_path + "err_source_node_id_invalid" + ".json"))
    assert output.value.args[0] == "The provided source_node_id is not in the node list."


def test_init_invalid_transformer_node_id():
    """
    A transformer is connected to a non-existent node.
         /--99
        /
    1--<9>  2--[10]--3------(16)
    ^       |
    20     [11]
            |
            4--[12]--5------(17)
            |
           [13]
            |
            6--[14]--7--[15]-8-----(19)
                     |
                    (18)
    """

    with pytest.raises(IDNotFoundError) as output:
        validate_power_grid_data(load_grid_json(base_test_data_path + "err_transformer_node_invalid" + ".json"))
    assert output.value.args[0] == "Transformer contains non-existent node ID."


def test_line_connected_to_same_node_both_sides():
    """
    Line 99 is connected to node 4 on both sides

    1--<9>--2--[10]-3------(16)
    ^       |
    20     [11]
            |
     [99]== 4--[12]-5------(17)
            |
           [13]
            |
            6--[14]-7--[15]-8-----(19)
                    |
                   (18)
    """

    with pytest.raises(IDNotUniqueError) as output:
        validate_power_grid_data(
            load_grid_json(base_test_data_path + "err_line_connected_both_sides_same_node" + ".json")
        )
    assert output.value.args[0] == "A line is connected to the same node on both sides."


def test_2_transformers():
    """
    2 transformers in the power grid.

    1--<9>--2--<10>-3------(16)
    ^       |
    20     [11]
            |
            4--[12]-5------(17)
            |
           [13]
            |
            6--[14]-7--[15]-8-----(19)
                    |
                   (18)
    """
    with pytest.raises(ValidationError) as output:
        validate_power_grid_data(load_grid_json(base_test_data_path + "err_2_transformers" + ".json"))
    assert (
        output.value.args[0]
        == "Transformer list contains more that 1 transformer. Only 1 transformer is supported for this object."
    )


def test_2_sources():
    """
    2 sources in the power grid.

    1--<9>--2--[10]-3------(16)
    ^       |
    20     [11]
            |
       99 > 4--[12]-5------(17)
            |
           [13]
            |
            6--[14]-7--[15]-8-----(19)
                    |
                   (18)
    """

    with pytest.raises(ValidationError) as output:
        validate_power_grid_data(load_grid_json(base_test_data_path + "err_2_sources" + ".json"))
    assert (
        output.value.args[0] == "Source list contains more that 1 source. Only 1 source is supported for this object."
    )


def test_load_and_validate_meta_data():
    """
    Test the metadata of the following grid on edge-cases.

    1--<9>--2--[10]-3------(16)
    ^       |
    20     [11]
            |
            4--[12]-5------(17)
            |
           [13]
            |
            6--[14]-7--[15]-8-----(19)
                    |
                   (18)
    """

    # normal initialization
    validate_meta_data(
        load_grid_json(base_test_data_path + "normal" + ".json"),
        load_meta_data_json(base_test_data_path + "normal_meta_data" + ".json"),
    )

    # test for invalid feeder id
    with pytest.raises(ValidationError) as output:
        validate_meta_data(
            load_grid_json(base_test_data_path + "normal" + ".json"),
            load_meta_data_json(base_test_data_path + "err_meta_data_invalid_feeder_id" + ".json"),
        )
    assert output.value.args[0] == "Feeder ID 4 is a non-existend line ID."

    # test for feeder not connected to busbar (output transformer)
    with pytest.raises(ValidationError) as output:
        validate_meta_data(
            load_grid_json(base_test_data_path + "normal" + ".json"),
            load_meta_data_json(base_test_data_path + "err_meta_data_not_connected_to_busbar" + ".json"),
        )
    assert output.value.args[0] == "Feeder ID 12 not connected to the transformer output (LV_busbar)."


def test_validate_ev_charging_profile():
    test_grid = PowerGrid(
        pgm_small_path, meta_data_small_path, p_profile_path=p_profile_small_path, q_profile_path=q_profile_small_path
    )

    validate_ev_charging_profile(test_grid, pd.read_parquet(ev_p_profile_small_path))

    with pytest.raises(ValidationError) as output:
        validate_ev_charging_profile(
            test_grid, pd.read_parquet(base_test_data_path + "err_ev_profile_too_few_profiles" + ".parquet")
        )
    assert (
        output.value.args[0]
        == "ev_charging_profile does not contain enough nodes for this power_grid (less power profiles than sym_loads)."
    )
