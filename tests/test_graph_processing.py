from contextlib import nullcontext as does_not_raise

import pytest

from power_system_simulation.data_validation import *
from power_system_simulation.exceptions import *
from power_system_simulation.graph_processing import (
    create_graph,
    filter_disabled_edges,
    find_alternative_edges,
    find_downstream_vertices,
    is_cyclic,
    is_edge_enabled,
    set_edge_enabled_status,
)


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

    nodes = [
        {"id": 1, "u_rated": 400},
        {"id": 2, "u_rated": 400},
        {"id": 3, "u_rated": 400},
        {"id": 4, "u_rated": 400},
        {"id": 5, "u_rated": 400},
        {"id": 6, "u_rated": 400},
        {"id": 7, "u_rated": 400},
        {"id": 8, "u_rated": 400},
    ]
    lines =  [
        {"id": 9, "from_node": 1, "to_node": 2, "from_status": 1, "to_status": 1},
        {"id": 10, "from_node": 2, "to_node": 3, "from_status": 1, "to_status": 1},
        {"id": 11, "from_node": 2, "to_node": 4, "from_status": 1, "to_status": 1},
        {"id": 12, "from_node": 4, "to_node": 5, "from_status": 1, "to_status": 1},
        {"id": 13, "from_node": 4, "to_node": 6, "from_status": 1, "to_status": 1},
        {"id": 14, "from_node": 6, "to_node": 7, "from_status": 1, "to_status": 1},
        {"id": 15, "from_node": 7, "to_node": 8, "from_status": 1, "to_status": 1}
    ]
    sym_loads =  [
        {"id": 16, "node": 3},
        {"id": 17, "node": 5},
        {"id": 18, "node": 7},
        {"id": 19, "node": 8}
    ]
    source = [
        {"id": 20, "node": 1}
    ]

    create_graph(nodes, lines, sym_loads, source)


def test_init_err1_duplicate_node_ids():
    """
    Duplicate node id 4, should raise an IDNotUniqueError.

    1--[9]--2--[10]-3------(16)
    ^       |
    20     [11]
            |
            4--[12]-4------(17)
            |
           [13]
            |
            6--[14]-7--[15]-8-----(19)
                    |
                   (18)
    """

    nodes = [
        {"id": 1, "u_rated": 400},
        {"id": 2, "u_rated": 400},
        {"id": 3, "u_rated": 400},
        {"id": 4, "u_rated": 400},
        {"id": 4, "u_rated": 400},
        {"id": 6, "u_rated": 400},
        {"id": 7, "u_rated": 400},
        {"id": 8, "u_rated": 400},
    ]
    lines =  [
        {"id": 9, "from_node": 1, "to_node": 2, "from_status": 1, "to_status": 1},
        {"id": 10, "from_node": 2, "to_node": 3, "from_status": 1, "to_status": 1},
        {"id": 11, "from_node": 2, "to_node": 4, "from_status": 1, "to_status": 1},
        {"id": 12, "from_node": 4, "to_node": 4, "from_status": 1, "to_status": 1},
        {"id": 13, "from_node": 4, "to_node": 6, "from_status": 1, "to_status": 1},
        {"id": 14, "from_node": 6, "to_node": 7, "from_status": 1, "to_status": 1},
        {"id": 15, "from_node": 7, "to_node": 8, "from_status": 1, "to_status": 1}
    ]
    sym_loads =  [
        {"id": 16, "node": 3},
        {"id": 17, "node": 4},
        {"id": 18, "node": 7},
        {"id": 19, "node": 8}
    ]
    source = [
        {"id": 20, "node": 1}
    ]

    with pytest.raises(IDNotUniqueError) as output:
        create_graph(nodes, lines, sym_loads, source)
    assert output.value.args[0] == "There are components with duplicate IDs."


def test_init_err1_duplicate_node_edge():
    """
    Duplicate edge ids, should raise an IDNotUniqueError.

    1--[9]--2--[7]-3------(16)
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

    nodes = [
        {"id": 1, "u_rated": 400},
        {"id": 2, "u_rated": 400},
        {"id": 3, "u_rated": 400},
        {"id": 4, "u_rated": 400},
        {"id": 5, "u_rated": 400},
        {"id": 6, "u_rated": 400},
        {"id": 7, "u_rated": 400},
        {"id": 8, "u_rated": 400},
    ]
    lines =  [
        {"id": 9, "from_node": 1, "to_node": 2, "from_status": 1, "to_status": 1},
        {"id": 7, "from_node": 2, "to_node": 3, "from_status": 1, "to_status": 1},
        {"id": 11, "from_node": 2, "to_node": 4, "from_status": 1, "to_status": 1},
        {"id": 12, "from_node": 4, "to_node": 5, "from_status": 1, "to_status": 1},
        {"id": 13, "from_node": 4, "to_node": 6, "from_status": 1, "to_status": 1},
        {"id": 14, "from_node": 6, "to_node": 7, "from_status": 1, "to_status": 1},
        {"id": 15, "from_node": 7, "to_node": 8, "from_status": 1, "to_status": 1}
    ]
    sym_loads =  [
        {"id": 16, "node": 3},
        {"id": 17, "node": 5},
        {"id": 18, "node": 7},
        {"id": 19, "node": 8}
    ]
    source = [
        {"id": 20, "node": 1}
    ]

    with pytest.raises(IDNotUniqueError) as output:
        create_graph(nodes, lines, sym_loads, source)
    assert output.value.args[0] == "There are components with duplicate IDs."


def test_init_err3_invalid_node_id():
    """
    A line is connected to a non-existent node.

    1--[9]--2--[10]-3------(16)
    ^       |
    20     [11]   /--16
            |    /
            4--[12]  5------(17)
            |
           [13]
            |
            6--[14]-7--[15]-8-----(19)
                    |
                   (18)
    """

    nodes = [
        {"id": 1, "u_rated": 400},
        {"id": 2, "u_rated": 400},
        {"id": 3, "u_rated": 400},
        {"id": 4, "u_rated": 400},
        {"id": 5, "u_rated": 400},
        {"id": 6, "u_rated": 400},
        {"id": 7, "u_rated": 400},
        {"id": 8, "u_rated": 400},
    ]
    lines =  [
        {"id": 9, "from_node": 1, "to_node": 2, "from_status": 1, "to_status": 1},
        {"id": 10, "from_node": 2, "to_node": 3, "from_status": 1, "to_status": 1},
        {"id": 11, "from_node": 2, "to_node": 4, "from_status": 1, "to_status": 1},
        {"id": 12, "from_node": 4, "to_node": 21, "from_status": 1, "to_status": 1},
        {"id": 13, "from_node": 4, "to_node": 6, "from_status": 1, "to_status": 1},
        {"id": 14, "from_node": 6, "to_node": 7, "from_status": 1, "to_status": 1},
        {"id": 15, "from_node": 7, "to_node": 8, "from_status": 1, "to_status": 1}
    ]
    sym_loads =  [
        {"id": 16, "node": 3},
        {"id": 17, "node": 5},
        {"id": 18, "node": 7},
        {"id": 19, "node": 8}
    ]
    source = [
        {"id": 20, "node": 1}
    ]

    with pytest.raises(IDNotFoundError) as output:
        create_graph(nodes, lines, sym_loads, source)
    assert output.value.args[0] == "Line(s) contain(s) non-existent node ID."


def test_init_err5_invalid_source_id():
    """
    The source ID is invalid.

    1--[9]--2--[10]-3------(16)     21
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

    nodes = [
        {"id": 1, "u_rated": 400},
        {"id": 2, "u_rated": 400},
        {"id": 3, "u_rated": 400},
        {"id": 4, "u_rated": 400},
        {"id": 5, "u_rated": 400},
        {"id": 6, "u_rated": 400},
        {"id": 7, "u_rated": 400},
        {"id": 8, "u_rated": 400},
    ]
    lines =  [
        {"id": 9, "from_node": 1, "to_node": 2, "from_status": 1, "to_status": 1},
        {"id": 10, "from_node": 2, "to_node": 3, "from_status": 1, "to_status": 1},
        {"id": 11, "from_node": 2, "to_node": 4, "from_status": 1, "to_status": 1},
        {"id": 12, "from_node": 4, "to_node": 5, "from_status": 1, "to_status": 1},
        {"id": 13, "from_node": 4, "to_node": 6, "from_status": 1, "to_status": 1},
        {"id": 14, "from_node": 6, "to_node": 7, "from_status": 1, "to_status": 1},
        {"id": 15, "from_node": 7, "to_node": 8, "from_status": 1, "to_status": 1}
    ]
    sym_loads =  [
        {"id": 16, "node": 3},
        {"id": 17, "node": 5},
        {"id": 18, "node": 7},
        {"id": 19, "node": 8}
    ]
    source = [
        {"id": 20, "node": 21}
    ]

    with pytest.raises(IDNotFoundError) as output:
        create_graph(nodes, lines, sym_loads, source)
    assert output.value.args[0] == "The provided source_node is not in the node list."


def test_init_err6_graph_not_connected_error():
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

    nodes = [
        {"id": 1, "u_rated": 400},
        {"id": 2, "u_rated": 400},
        {"id": 3, "u_rated": 400},
        {"id": 4, "u_rated": 400},
        {"id": 5, "u_rated": 400},
        {"id": 6, "u_rated": 400},
        {"id": 7, "u_rated": 400},
        {"id": 8, "u_rated": 400},
    ]
    lines =  [
        {"id": 9, "from_node": 1, "to_node": 2, "from_status": 1, "to_status": 1},
        {"id": 10, "from_node": 2, "to_node": 3, "from_status": 1, "to_status": 1},
        {"id": 11, "from_node": 2, "to_node": 4, "from_status": 1, "to_status": 1},
        {"id": 12, "from_node": 4, "to_node": 5, "from_status": 1, "to_status": 1},
        {"id": 14, "from_node": 6, "to_node": 7, "from_status": 1, "to_status": 1},
        {"id": 15, "from_node": 7, "to_node": 8, "from_status": 1, "to_status": 1}
    ]
    sym_loads =  [
        {"id": 16, "node": 3},
        {"id": 17, "node": 5},
        {"id": 18, "node": 7},
        {"id": 19, "node": 8}
    ]
    source = [
        {"id": 20, "node": 1}
    ]

    with pytest.raises(GraphNotFullyConnectedError) as output:
        create_graph(nodes, lines, sym_loads, source)
    assert output.value.args[0] == "The graph is not fully connected."


def test_init_err6_graph_not_connected_disabled_error():
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

    nodes = [
        {"id": 1, "u_rated": 400},
        {"id": 2, "u_rated": 400},
        {"id": 3, "u_rated": 400},
        {"id": 4, "u_rated": 400},
        {"id": 5, "u_rated": 400},
        {"id": 6, "u_rated": 400},
        {"id": 7, "u_rated": 400},
        {"id": 8, "u_rated": 400},
    ]
    lines =  [
        {"id": 9, "from_node": 1, "to_node": 2, "from_status": 1, "to_status": 1},
        {"id": 10, "from_node": 2, "to_node": 3, "from_status": 1, "to_status": 1},
        {"id": 11, "from_node": 2, "to_node": 4, "from_status": 0, "to_status": 1},
        {"id": 12, "from_node": 4, "to_node": 5, "from_status": 1, "to_status": 1},
        {"id": 13, "from_node": 4, "to_node": 6, "from_status": 1, "to_status": 1},
        {"id": 14, "from_node": 6, "to_node": 7, "from_status": 1, "to_status": 1},
        {"id": 15, "from_node": 7, "to_node": 8, "from_status": 1, "to_status": 1}
    ]
    sym_loads =  [
        {"id": 16, "node": 3},
        {"id": 17, "node": 5},
        {"id": 18, "node": 7},
        {"id": 19, "node": 8}
    ]
    source = [
        {"id": 20, "node": 1}
    ]

    with pytest.raises(GraphNotFullyConnectedError) as output:
        create_graph(nodes, lines, sym_loads, source)
    assert output.value.args[0] == "The graph is not fully connected."


def test_init_err7_graph_contains_cycle_error():
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

    nodes = [
        {"id": 1, "u_rated": 400},
        {"id": 2, "u_rated": 400},
        {"id": 3, "u_rated": 400},
        {"id": 4, "u_rated": 400},
        {"id": 5, "u_rated": 400},
        {"id": 6, "u_rated": 400},
        {"id": 7, "u_rated": 400},
        {"id": 8, "u_rated": 400},
    ]
    lines =  [
        {"id": 9, "from_node": 1, "to_node": 2, "from_status": 1, "to_status": 1},
        {"id": 10, "from_node": 2, "to_node": 3, "from_status": 1, "to_status": 1},
        {"id": 11, "from_node": 2, "to_node": 4, "from_status": 1, "to_status": 1},
        {"id": 12, "from_node": 4, "to_node": 5, "from_status": 1, "to_status": 1},
        {"id": 13, "from_node": 4, "to_node": 6, "from_status": 1, "to_status": 1},
        {"id": 14, "from_node": 6, "to_node": 7, "from_status": 1, "to_status": 1},
        {"id": 15, "from_node": 7, "to_node": 8, "from_status": 1, "to_status": 1},
        {"id": 21, "from_node": 3, "to_node": 5, "from_status": 1, "to_status": 1}
    ]
    sym_loads =  [
        {"id": 16, "node": 3},
        {"id": 17, "node": 5},
        {"id": 18, "node": 7},
        {"id": 19, "node": 8}
    ]
    source = [
        {"id": 20, "node": 1}
    ]

    with pytest.raises(GraphCycleError) as output:
        create_graph(nodes, lines, sym_loads, source)
    assert output.value.args[0] == "The graph contains a cycle."


def test_init_err7_graph_contains_cycle_disabled_error():
    """
    The graph contains a cycle, but the cycle is broken by a disabled edge, which is allowed. This should not raise
    an error.

    1--[9]--2--[10]-3------(16)
    ^       |       
    20     [11]    [21]
            |       
            4--[12]-5------(17)
            |
           [13]
            |
            6--[14]-7--[15]-8-----(19)
                    |
                   (18)
    """

    nodes = [
        {"id": 1, "u_rated": 400},
        {"id": 2, "u_rated": 400},
        {"id": 3, "u_rated": 400},
        {"id": 4, "u_rated": 400},
        {"id": 5, "u_rated": 400},
        {"id": 6, "u_rated": 400},
        {"id": 7, "u_rated": 400},
        {"id": 8, "u_rated": 400},
    ]
    lines =  [
        {"id": 9, "from_node": 1, "to_node": 2, "from_status": 1, "to_status": 1},
        {"id": 10, "from_node": 2, "to_node": 3, "from_status": 1, "to_status": 1},
        {"id": 11, "from_node": 2, "to_node": 4, "from_status": 1, "to_status": 1},
        {"id": 12, "from_node": 4, "to_node": 5, "from_status": 1, "to_status": 1},
        {"id": 13, "from_node": 4, "to_node": 6, "from_status": 1, "to_status": 1},
        {"id": 14, "from_node": 6, "to_node": 7, "from_status": 1, "to_status": 1},
        {"id": 15, "from_node": 7, "to_node": 8, "from_status": 1, "to_status": 1},
        {"id": 21, "from_node": 3, "to_node": 5, "from_status": 1, "to_status": 0}
    ]
    sym_loads =  [
        {"id": 16, "node": 3},
        {"id": 17, "node": 5},
        {"id": 18, "node": 7},
        {"id": 19, "node": 8}
    ]
    source = [
        {"id": 20, "node": 1}
    ]

    create_graph(nodes, lines, sym_loads, source)


def test_is_edge_enabled():
    """
    The chosen edge is either enabled or disabled, or not a valid edge_id.

    15> 1--[6]--2--[7]--3------(12)
        |
        |      [10]
        |
        ---[8]--4------(13)
        |
        |      [11]
        |
        ---[9]--5------(14)

    """

    nodes = [
        {"id": 1, "u_rated": 400},
        {"id": 2, "u_rated": 400},
        {"id": 3, "u_rated": 400},
        {"id": 4, "u_rated": 400},
        {"id": 5, "u_rated": 400}
    ]
    lines =  [
        {"id": 6, "from_node": 1, "to_node": 2, "from_status": 1, "to_status": 1},
        {"id": 7, "from_node": 2, "to_node": 3, "from_status": 1, "to_status": 1},
        {"id": 8, "from_node": 1, "to_node": 4, "from_status": 1, "to_status": 1},
        {"id": 9, "from_node": 1, "to_node": 5, "from_status": 1, "to_status": 1},
        {"id": 10, "from_node": 2, "to_node": 4, "from_status": 0, "to_status": 0},
        {"id": 11, "from_node": 4, "to_node": 5, "from_status": 0, "to_status": 0}
    ]
    sym_loads =  [
        {"id": 12, "node": 3},
        {"id": 13, "node": 4},
        {"id": 14, "node": 5}
    ]
    source = [
        {"id": 15, "node": 1}
    ]

    test = create_graph(nodes, lines, sym_loads, source)

    # Test if edges are enabled or disabled
    assert is_edge_enabled(test, 7) == True
    assert is_edge_enabled(test, 10) == False

    # Test if error is raised if chosen edge is not a valid ID
    with pytest.raises(IDNotFoundError) as output:
        is_edge_enabled(test, 12)
    assert output.value.args[0] == "The chosen edge 10 is not in the ID list."


def test_find_downstream_vertices_normal_case():
    """
    Test normal case where edge is enabled and has downstream vertices.

    1--[6]--2--[7]--3------(10)
    ^       |
    12     [8]
            |
            4--[9]--5------(11)
    """

    nodes = [
        {"id": 1, "u_rated": 400},
        {"id": 2, "u_rated": 400},
        {"id": 3, "u_rated": 400},
        {"id": 4, "u_rated": 400},
        {"id": 5, "u_rated": 400}
    ]
    lines =  [
        {"id": 6, "from_node": 1, "to_node": 2, "from_status": 1, "to_status": 1},
        {"id": 7, "from_node": 2, "to_node": 3, "from_status": 1, "to_status": 1},
        {"id": 8, "from_node": 2, "to_node": 4, "from_status": 1, "to_status": 1},
        {"id": 9, "from_node": 4, "to_node": 5, "from_status": 1, "to_status": 1}
    ]
    sym_loads =  [
        {"id": 10, "node": 3},
        {"id": 11, "node": 5}
    ]
    source = [
        {"id": 12, "node": 1}
    ]
    
    test = create_graph(nodes, lines, sym_loads, source)

    # Test edge 1 (1-2) - downstream should be 2,3,4,5
    assert sorted(find_downstream_vertices(test, 6)) == [2, 3, 4, 5]

    # Test edge 2 (2-3) - downstream should be 3
    assert find_downstream_vertices(test, 7) == [3]

    # Test edge 3 (2-4) - downstream should be 4,5
    assert sorted(find_downstream_vertices(test, 8)) == [4, 5]

    # Test edge 4 (4-5) - downstream should be 5
    assert find_downstream_vertices(test, 9) == [5]


def test_find_downstream_vertices_disabled_case():
    """
    Test for downstream vertices

    0--[1]--2--[9]--10
    ^
    |      [7]
    |
    ---[3]--4
    |
    |      [8]
    |
    ---[5]--6

    """

    vertex_ids = [0, 2, 4, 6, 10]
    edge_ids = [1, 3, 5, 7, 8, 9]
    edge_vertex_id_pairs = [(0, 2), (0, 4), (0, 6), (2, 4), (4, 6), (2, 10)]
    edge_enabled = [True, True, True, False, False, True]
    source_vertex_id = 0

    test = create_graph(vertex_ids, edge_ids, edge_vertex_id_pairs, edge_enabled, source_vertex_id)

    # Source node 0
    assert sorted(find_downstream_vertices(test, 1)) == [2, 10]
    assert find_downstream_vertices(test, 9) == [10]
    assert find_downstream_vertices(test, 7) == []

    # Invalid edge_id
    with pytest.raises(IDNotFoundError) as output:
        find_downstream_vertices(test, 2)
        assert output.value.args[0] == "The provided ID is not in the edge_ids list."

    # Source node 10
    test.graph["source_vertex_id"] = 10
    assert sorted(find_downstream_vertices(test, 9)) == [0, 2, 4, 6]


def test_edge_set_to_correct_enabled_status():
    """
    Tests that the edge is correctly set to enabled or disabled
    and an error is given if edge is already disabled or not a valid id.

    0--[1]--2--[9]--10
    ^
    |      [7]
    |
    ---[3]--4
    |
    |      [8]
    |
    ---[5]--6

    """

    vertex_ids = [0, 2, 4, 6, 10]
    edge_ids = [1, 3, 5, 7, 8, 9]
    edge_vertex_id_pairs = [(0, 2), (0, 4), (0, 6), (2, 4), (4, 6), (2, 10)]
    edge_enabled = [True, True, True, False, False, True]
    source_vertex_id = 0

    test = create_graph(vertex_ids, edge_ids, edge_vertex_id_pairs, edge_enabled, source_vertex_id)

    # Test if edge 1 is correctly disabled
    set_edge_enabled_status(test, 1, False)
    assert is_edge_enabled(test,1) == False

    # Test if error is raised if chosen edge is already disabled
    with pytest.raises(EdgeAlreadyDisabledError) as output:
        set_edge_enabled_status(test, 7, False)
        assert output.value.args[0] == "The chosen edge 7 is already disabled."

    # Test if error is raised if chosen edge is not a valid ID
    with pytest.raises(IDNotFoundError) as output:
        set_edge_enabled_status(test, 10, False)
        assert output.value.args[0] == "The chosen edge 10 is not in the ID list."

    # Test if edge 7 is actually enabled
    set_edge_enabled_status(test, 7, True)
    assert is_edge_enabled(test,7) == True


def test_find_alternative_edges_err1():
    """
    Tests that alternative edges are found

    0--[1]--2--[9]--10
    ^
    |      [7]
    |
    ---[3]--4
    |
    |      [8]
    |
    ---[5]--6

    """
    vertex_ids = [0, 2, 4, 6, 10]
    edge_ids = [1, 3, 5, 7, 8, 9]
    edge_vertex_id_pairs = [(0, 2), (0, 4), (0, 6), (2, 4), (4, 6), (2, 10)]
    edge_enabled = [True, True, True, False, False, True]
    source_vertex_id = 0

    test = create_graph(vertex_ids, edge_ids, edge_vertex_id_pairs, edge_enabled, source_vertex_id)

    # tests if found alternative edges for disabled edge input are correct (connect the graph and acyclic)
    assert find_alternative_edges(test, 1) == [7]
    assert find_alternative_edges(test, 3) == [7, 8]
    assert find_alternative_edges(test, 5) == [8]
    assert find_alternative_edges(test, 9) == []

    # Test if error is raised if chosen edge is already disabled
    with pytest.raises(EdgeAlreadyDisabledError) as output:
        find_alternative_edges(test, 7)
        assert output.value.args[0] == "The chosen edge 7 is already disabled."

    # Test if error is raised if chosen edge is not a valid ID
    with pytest.raises(IDNotFoundError) as output:
        find_alternative_edges(test, 10)
        assert output.value.args[0] == "The chosen edge 10 is not in the ID list."
