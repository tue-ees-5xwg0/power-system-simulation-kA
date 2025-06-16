from contextlib import nullcontext as does_not_raise

import pytest

from power_system_simulation.exceptions import *
from power_system_simulation.input_data_validation import *

base_test_data_path = "tests/test_data/incorrect_power_grids/"


def test_init_err1_duplicate_node_ids():
    """
    Duplicate node id 4, should raise an IDNotUniqueError.

    1--[9]--2--[10]-3------(16)
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


def test_init_err3_invalid_sym_load_node_id():
    """
    A sym_load is connected to a non-existent node.

    1--[9]--2--[7]-3        99------(16)
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


def test_init_err3_invalid_line_node_id():
    """
    A line is connected to a non-existent node.

    1--[9]--2--[10]-3------(16)
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


def test_init_err5_invalid_source_node_id():
    """
    The source ID is invalid.

    1--[9]--2--[10]-3------(16)     99
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

