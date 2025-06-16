from contextlib import nullcontext as does_not_raise

import pytest
from power_grid_model.utils import json_deserialize

from power_system_simulation.exceptions import *
from power_system_simulation.graph_processing import *

base_test_data_path = "tests/test_data/incorrect_power_grids/"


def test_init_normal():
    """
    Normal initialization of a graph processor, should result in no errors.

    1--[9]--2--[10]-3------(16)
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

    with open(base_test_data_path + "normal" + ".json", "r", encoding="utf-8") as file:
        power_grid = json_deserialize(file.read())
    create_graph(power_grid)


def test_init_graph_not_connected_error():
    """
    One of the edges is missing, causing the graph to not be fully connected. Should raise a
    GraphNotFullyConnectedError.

    1--[9]--2--[10]-3------(16)
    ^       |
    20     [11]
            |
            4--[12]-5------(17)



            6--[14]-7--[15]-8-----(19)
                    |
                   (18)
    """

    with open(base_test_data_path + "err_graph_not_connected" + ".json", "r", encoding="utf-8") as file:
        power_grid = json_deserialize(file.read())

    with pytest.raises(GraphNotFullyConnectedError) as output:
        create_graph(power_grid)
    assert output.value.args[0] == "The graph is not fully connected."


def test_init_graph_not_connected_disabled_error():
    """
    One of the edges is disabled, causing the graph to not be fully connected. Should raise a
    GraphNotFullyConnectedError.

    1--[9]--2--[10]-3------(16)
    ^
    20     [11]

            4--[12]-5------(17)
            |
           [13]
            |
            6--[14]-7--[15]-8-----(19)
                    |
                   (18)
    """

    with open(base_test_data_path + "err_graph_not_connected" + ".json", "r", encoding="utf-8") as file:
        power_grid = json_deserialize(file.read())

    with pytest.raises(GraphNotFullyConnectedError) as output:
        create_graph(power_grid)
    assert output.value.args[0] == "The graph is not fully connected."


def test_init_graph_contains_cycle_error():
    """
    The graph contains a cycle, which is not allowed. This should raise a GraphCycleError.

    1--[9]--2--[10]-3------(16)
    ^       |       |
    20     [11]    [21]
            |       |
            4--[12]-5------(17)
            |
           [13]
            |
            6--[14]-7--[15]-8-----(19)
                    |
                   (18)
    """

    with open(base_test_data_path + "err_graph_cycle" + ".json", "r", encoding="utf-8") as file:
        power_grid = json_deserialize(file.read())

    with pytest.raises(GraphCycleError) as output:
        create_graph(power_grid)
    assert output.value.args[0] == "The graph contains a cycle."


def test_init_graph_contains_cycle_disabled():
    """
    The graph contains a cycle, but the cycle is broken by a disabled edge, which is allowed. This should not raise
    an error.

    1--[9]--2--[10]-3------(16)
    ^       |
    20     [11]    [21]
            |
            4--[12]-5------(17)
            |
           [13]    [22]
            |
            6--[14]-7--[15]-8-----(19)
                    |
                   (18)
    """

    with open(base_test_data_path + "graph_cycle_disabled" + ".json", "r", encoding="utf-8") as file:
        power_grid = json_deserialize(file.read())

    create_graph(power_grid)


def test_filter_disabled_edges():
    """
    Returns a graph with all edges removed, and a version with all edges and sym_loads removed.

    1--[9]--2--[10]-3------(16)
    ^       |
    20     [11]    [21]
            |
            4--[12]-5------(17)
            |
           [13]    [22]
            |
            6--[14]-7--[15]-8-----(19)
                    |
                   (18)
    """

    with open(base_test_data_path + "graph_cycle_disabled" + ".json", "r", encoding="utf-8") as file:
        power_grid = json_deserialize(file.read())
    with open(base_test_data_path + "graph_cycle_disabled_filtered" + ".json", "r", encoding="utf-8") as file:
        power_grid_filtered = json_deserialize(file.read())
    with open(
        base_test_data_path + "graph_cycle_disabled_filtered_no_sym_loads" + ".json", "r", encoding="utf-8"
    ) as file:
        power_grid_filtered_no_sym_loads = json_deserialize(file.read())

    test_graph_filtered = filter_disabled_edges(create_graph(power_grid))
    test_graph_filtered_no_sym_loads = filter_disabled_edges(create_graph(power_grid), True)

    control_graph = create_graph(power_grid_filtered)
    control_graph_no_sym_loads = create_graph(power_grid_filtered_no_sym_loads)

    assert test_graph_filtered.nodes == control_graph.nodes
    assert test_graph_filtered.edges == control_graph.edges
    assert not is_cyclic(test_graph_filtered)
    assert nx.is_connected(test_graph_filtered)

    assert test_graph_filtered_no_sym_loads.nodes == control_graph_no_sym_loads.nodes
    assert test_graph_filtered_no_sym_loads.edges == control_graph_no_sym_loads.edges
    assert not is_cyclic(test_graph_filtered_no_sym_loads)
    assert nx.is_connected(test_graph_filtered_no_sym_loads)


def test_is_edge_enabled():
    """
    The chosen edge is either enabled or disabled, or not a valid edge_id.

    1--[9]--2--[10]-3------(16)
    ^       |
    20     [11]    [21]
            |
            4--[12]-5------(17)
            |
           [13]    [22]
            |
            6--[14]-7--[15]-8-----(19)
                    |
                   (18)
    """

    with open(base_test_data_path + "graph_cycle_disabled" + ".json", "r", encoding="utf-8") as file:
        power_grid = json_deserialize(file.read())
    test = create_graph(power_grid)

    # test if edges are enabled or disabled
    assert is_edge_enabled(test, 9) == True
    assert is_edge_enabled(test, 21) == False

    # test if error is raised if chosen edge is not a valid ID
    with pytest.raises(IDNotFoundError) as output:
        is_edge_enabled(test, 99)
    assert output.value.args[0] == "The provided edge 99 is not in the ID list."


def test_find_downstream_vertices_normal_case():
    """
    Test normal case where edge is enabled and has downstream vertices.

    1--[9]--2--[10]-3------(16)
    ^       |
    20     [11]    [21]
            |
            4--[12]-5------(17)
            |
           [13]    [22]
            |
            6--[14]-7--[15]-8-----(19)
                    |
                   (18)
    """

    with open(base_test_data_path + "graph_cycle_disabled" + ".json", "r", encoding="utf-8") as file:
        power_grid = json_deserialize(file.read())
    test = create_graph(power_grid)

    # exclude sym_load nodes
    assert find_downstream_vertices(test, 9) == [2, 3, 4, 5, 6, 7, 8]
    assert find_downstream_vertices(test, 14) == [7, 8]
    assert find_downstream_vertices(test, 21) == []
    assert find_downstream_vertices(test, 11) == [4, 5, 6, 7, 8]

    # include sym_load nodes
    assert find_downstream_vertices(test, 11, False) == [4, 5, 6, 7, 8, 17, 18, 19]

    # test from different source_node
    test.graph["source_node_id"] = 4
    assert find_downstream_vertices(test, 11) == [1, 2, 3]
    assert find_downstream_vertices(test, 12) == [5]

    # test invalid source node
    test.graph["source_node_id"] = 99
    with pytest.raises(IDNotFoundError) as output:
        find_downstream_vertices(test, 9)
    assert output.value.args[0] == "source_node_id is non-existent."


def test_edge_set_to_correct_enabled_status():
    """
    Tests that the edge is correctly set to enabled or disabled
    and an error is given if edge is already disabled or not a valid id.

    1--[9]--2--[10]-3------(16)
    ^       |
    20     [11]    [21]
            |
            4--[12]-5------(17)
            |
           [13]    [22]
            |
            6--[14]-7--[15]-8-----(19)
                    |
                   (18)
    """

    with open(base_test_data_path + "graph_cycle_disabled" + ".json", "r", encoding="utf-8") as file:
        power_grid = json_deserialize(file.read())
    test = create_graph(power_grid)

    set_edge_enabled_status(test, 9, False)
    assert is_edge_enabled(test, 9) == False
    set_edge_enabled_status(test, 12, False)
    assert is_edge_enabled(test, 12) == False

    # Test if error is raised if chosen edge is already disabled
    with pytest.raises(EdgeAlreadyDisabledError) as output:
        set_edge_enabled_status(test, 12, False)
    assert output.value.args[0] == "The chosen edge 12 is already disabled."

    # Test if error is raised if chosen edge is not a valid ID
    with pytest.raises(IDNotFoundError) as output:
        set_edge_enabled_status(test, 999, False)
    assert output.value.args[0] == "The chosen edge 999 is not in the ID list."

    # Test if edge 7 is actually enabled
    set_edge_enabled_status(test, 21, True)
    assert is_edge_enabled(test, 21) == True


def test_find_alternative_edges():
    """
    Tests that alternative edges are found

    1--[9]--2--[10]-3------(16)
    ^       |
    20     [11]    [21]
            |
            4--[12]-5------(17)
            |
           [13]    [22]
            |
            6--[14]-7--[15]-8-----(19)
                    |
                   (18)
    """

    with open(base_test_data_path + "graph_cycle_disabled" + ".json", "r", encoding="utf-8") as file:
        power_grid = json_deserialize(file.read())
    test = create_graph(power_grid)

    # tests if found alternative edges for disabled edge input are correct (connect the graph and acyclic)
    assert find_alternative_edges(test, 10) == [21]
    assert find_alternative_edges(test, 12) == [21, 22]
    assert find_alternative_edges(test, 11) == [21]
    assert find_alternative_edges(test, 14) == [22]
    assert find_alternative_edges(test, 15) == []
    assert find_alternative_edges(test, 9) == []

    # Test if error is raised if chosen edge is already disabled
    with pytest.raises(EdgeAlreadyDisabledError) as output:
        find_alternative_edges(test, 21)
    assert output.value.args[0] == "The chosen edge 21 is already disabled."

    # Test if error is raised if chosen edge is not a valid ID
    with pytest.raises(IDNotFoundError) as output:
        find_alternative_edges(test, 2)
    assert output.value.args[0] == "The chosen edge 2 is not in the ID list."
