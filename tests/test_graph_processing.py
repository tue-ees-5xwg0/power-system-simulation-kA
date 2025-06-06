from contextlib import nullcontext as does_not_raise

import pytest

import power_system_simulation.graph_processing as gp


def test_init_normal():
    """
    Normal initialization of a graph processor, should result in no errors.

    1--[1]--2--[2]--3
    ^       |
           [3]
            |
            4--[4]--5
            |
           [5]
            |
            6--[6]--7--[7]--8
    """

    vertex_ids = [1, 2, 3, 4, 5, 6, 7, 8]
    edge_ids = [1, 2, 3, 4, 5, 6, 7]
    edge_vertex_id_pairs = [(1, 2), (2, 3), (2, 4), (4, 5), (4, 6), (6, 7), (7, 8)]
    edge_enabled = [True, True, True, True, True, True, True]
    source_vertex_id = 1

    gp.GraphProcessor(vertex_ids, edge_ids, edge_vertex_id_pairs, edge_enabled, source_vertex_id)


def test_init_err1_duplicate_vertex_ids():
    """
    Duplicate vertex ids, should raise an IDNotUniqueError.

    1--[1]--2--[2]--3
    ^       |
           [3]
            |
           (4)-[4]-(4)
            |
           [5]
            |
            6--[6]--7--[7]--8
    """

    vertex_ids = [1, 2, 3, 4, 4, 6, 7, 8]
    edge_ids = [1, 2, 3, 4, 5, 6, 7]
    edge_vertex_id_pairs = [(1, 2), (2, 3), (2, 4), (4, 4), (4, 6), (6, 7), (7, 8)]
    edge_enabled = [True, True, True, True, True, True, True]
    source_vertex_id = 1

    with pytest.raises(gp.IDNotUniqueError) as output:
        gp.GraphProcessor(vertex_ids, edge_ids, edge_vertex_id_pairs, edge_enabled, source_vertex_id)
        assert output.value.args[0] == "Input list vertex_ids contains a duplicate id."


def test_init_err1_duplicate_edge_ids():
    """
    Duplicate edge ids, should raise an IDNotUniqueError.

    1--[1]--2--[2]--3
    ^       |
           [3]
            |
            4--[4]--5
            |
           (6)
            |
            6--(6)--7--[7]--8
    """

    vertex_ids = [1, 2, 3, 4, 5, 6, 7, 8]
    edge_ids = [1, 2, 3, 4, 6, 6, 7]
    edge_vertex_id_pairs = [(1, 2), (2, 3), (2, 4), (4, 5), (4, 6), (6, 7), (7, 8)]
    edge_enabled = [True, True, True, True, True, True, True]
    source_vertex_id = 1

    with pytest.raises(gp.IDNotUniqueError) as output:
        gp.GraphProcessor(vertex_ids, edge_ids, edge_vertex_id_pairs, edge_enabled, source_vertex_id)
        assert output.value.args[0] == "Input list edge_ids contains a duplicate id."


def test_init_err2_id_pair_length_mismatch():
    """
    One of the edges has no edge_vertex_id_pair, or one too many id_pairs is entered and thus should result
    in a length mismatch error.

    1--[1]--2  [2]  3
    ^       |
           [3]
            |
            4--[4]--5
            |
           [5]
            |
            6--[6]--7--[7]--8
    """

    vertex_ids = [1, 2, 3, 4, 5, 6, 7, 8]
    edge_ids = [1, 2, 3, 4, 5, 6, 7]
    edge_vertex_id_pairs = [(1, 2), (2, 4), (4, 5), (4, 6), (6, 7), (7, 8)]
    edge_enabled = [True, True, True, True, True, True, True]
    source_vertex_id = 1

    with pytest.raises(gp.InputLengthDoesNotMatchError) as output:
        gp.GraphProcessor(vertex_ids, edge_ids, edge_vertex_id_pairs, edge_enabled, source_vertex_id)
        assert output.value.args[0] == "The length of edge_ids does not match the length of edge_vertex_id_pairs."


def test_init_err3_invalid_id_pair_id():
    """
    An edge_vertex_id_pair is referring to a non-existent vertex.

    1--[1]--2--[2]--3
    ^       |
           [3]   (9)
            |    /
            4--[4]  5
            |
           [5]
            |
            6--[6]--7--[7]--8
    """

    vertex_ids = [1, 2, 3, 4, 5, 6, 7, 8]
    edge_ids = [1, 2, 3, 4, 5, 6, 7]
    edge_vertex_id_pairs = [(1, 2), (2, 3), (2, 4), (4, 9), (4, 6), (6, 7), (7, 8)]
    edge_enabled = [True, True, True, True, True, True, True]
    source_vertex_id = 1

    with pytest.raises(gp.IDNotFoundError) as output:
        gp.GraphProcessor(vertex_ids, edge_ids, edge_vertex_id_pairs, edge_enabled, source_vertex_id)
        assert output.value.args[0] == "edge_vertex_id_pairs contains a non-existent vertex ID."


def test_init_err4_edge_enabled_length_mismatch():
    """
    The edge_enabled list contains too many or few entries, and should thus return a length mismatch error.

    1--[1]--2--[2]--3
    ^       |
           [3]
            |
            4--[4]--5
            |
           [5]
            |
            6--[6]--7--[7]--8
    """

    vertex_ids = [1, 2, 3, 4, 5, 6, 7, 8]
    edge_ids = [1, 2, 3, 4, 5, 6, 7]
    edge_vertex_id_pairs = [(1, 2), (2, 3), (2, 4), (4, 5), (4, 6), (6, 7), (7, 8)]
    edge_enabled = [True, True, True, True, True, True, True, True]
    source_vertex_id = 1

    with pytest.raises(gp.InputLengthDoesNotMatchError) as output:
        gp.GraphProcessor(vertex_ids, edge_ids, edge_vertex_id_pairs, edge_enabled, source_vertex_id)
        assert output.value.args[0] == "The length of edge_ids does not match the length of edge_enabled."


def test_init_err5_invalid_source_id():
    """
    The source ID is invalid.

    1--[1]--2--[2]--3
            |
    (9)    [3]
     ^      |
            4--[4]--5
            |
           [5]
            |
            6--[6]--7--[7]--8
    """

    vertex_ids = [1, 2, 3, 4, 5, 6, 7, 8]
    edge_ids = [1, 2, 3, 4, 5, 6, 7]
    edge_vertex_id_pairs = [(1, 2), (2, 3), (2, 4), (4, 5), (4, 6), (6, 7), (7, 8)]
    edge_enabled = [True, True, True, True, True, True, True]
    source_vertex_id = 9

    with pytest.raises(gp.IDNotFoundError) as output:
        gp.GraphProcessor(vertex_ids, edge_ids, edge_vertex_id_pairs, edge_enabled, source_vertex_id)
        assert output.value.args[0] == "The provided source_vertex_id is not in the vertex_ids list."


def test_init_err6_graph_not_connected_error():
    """
    One of the edges is missing, causing the graph to not be fully connected. Should raise a
    GraphNotFullyConnectedError.

    1--[1]--2--[2]--3
    ^       |
           [3]
            |
            4--[4]--5



            6--[6]--7--[7]--8
    """

    vertex_ids = [1, 2, 3, 4, 5, 6, 7, 8]
    edge_ids = [1, 2, 3, 4, 6, 7]
    edge_vertex_id_pairs = [(1, 2), (2, 3), (2, 4), (4, 5), (6, 7), (7, 8)]
    edge_enabled = [True, True, True, True, True, True]
    source_vertex_id = 1

    with pytest.raises(gp.GraphNotFullyConnectedError) as output:
        gp.GraphProcessor(vertex_ids, edge_ids, edge_vertex_id_pairs, edge_enabled, source_vertex_id)
        assert output.value.args[0] == "The graph is not fully connected."


def test_init_err6_graph_not_connected_disabled_error():
    """
    One of the edges is disabled, causing the graph to not be fully connected. Should raise a
    GraphNotFullyConnectedError.

    1--[1]--2--[2]--3
    ^       |
           [3]
            |
            4--[4]--5

           [5]

            6--[6]--7--[7]--8
    """

    vertex_ids = [1, 2, 3, 4, 5, 6, 7, 8]
    edge_ids = [1, 2, 3, 4, 5, 6, 7]
    edge_vertex_id_pairs = [(1, 2), (2, 3), (2, 4), (4, 5), (4, 6), (6, 7), (7, 8)]
    edge_enabled = [True, True, True, True, False, True, True]
    source_vertex_id = 1

    with pytest.raises(gp.GraphNotFullyConnectedError) as output:
        gp.GraphProcessor(vertex_ids, edge_ids, edge_vertex_id_pairs, edge_enabled, source_vertex_id)
        assert output.value.args[0] == "The graph is not fully connected."


def test_init_err7_graph_contains_cycle_error():
    """
    The graph contains a cycle, which is not allowed. This should raise a GraphCycleError.

    1--[1]--2--[2]--3
    ^       |
           [3]
            |
            4--[4]--5
            |       |
           [5]     [8]
            |       |
            6--[6]--7--[7]--8
    """

    vertex_ids = [1, 2, 3, 4, 5, 6, 7, 8]
    edge_ids = [1, 2, 3, 4, 5, 6, 7, 8]
    edge_vertex_id_pairs = [(1, 2), (2, 3), (2, 4), (4, 5), (4, 6), (6, 7), (7, 8), (5, 7)]
    edge_enabled = [True, True, True, True, True, True, True, True]
    source_vertex_id = 1

    with pytest.raises(gp.GraphCycleError) as output:
        gp.GraphProcessor(vertex_ids, edge_ids, edge_vertex_id_pairs, edge_enabled, source_vertex_id)
        assert output.value.args[0] == "The graph contains a cycle."


def test_init_err7_graph_contains_cycle_disabled_error():
    """
    The graph contains a cycle, but the cycle is broken by a disabled edge, which is allowed. This should not raise
    an error.

    1--[1]--2--[2]--3
    ^       |
           [3]
            |
            4--[4]--5
            |
           [5]     [8]
            |
            6--[6]--7--[7]--8
    """

    vertex_ids = [1, 2, 3, 4, 5, 6, 7, 8]
    edge_ids = [1, 2, 3, 4, 5, 6, 7, 8]
    edge_vertex_id_pairs = [(1, 2), (2, 3), (2, 4), (4, 5), (4, 6), (6, 7), (7, 8), (5, 7)]
    edge_enabled = [True, True, True, True, True, True, True, False]
    source_vertex_id = 1

    gp.GraphProcessor(vertex_ids, edge_ids, edge_vertex_id_pairs, edge_enabled, source_vertex_id)


def test_is_edge_enabled():
    """
    The chosen edge is either enabled or disabled, or not a valid edge_id.

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

    test = gp.GraphProcessor(vertex_ids, edge_ids, edge_vertex_id_pairs, edge_enabled, source_vertex_id)

    # Test if edges are enabled or disabled
    assert test.is_edge_enabled(3) == True
    assert test.is_edge_enabled(7) == False

    # Test if error is raised if chosen edge is not a valid ID
    with pytest.raises(gp.IDNotFoundError) as output:
        test.is_edge_enabled(10)
        assert output.value.args[0] == "The chosen edge 10 is not in the ID list."


def test_find_downstream_vertices_normal_case():
    """
    Test normal case where edge is enabled and has downstream vertices.

    1--[1]--2--[2]--3
    ^       |
           [3]
            |
            4--[4]--5
    """

    vertex_ids = [1, 2, 3, 4, 5]
    edge_ids = [1, 2, 3, 4]
    edge_vertex_id_pairs = [(1, 2), (2, 3), (2, 4), (4, 5)]
    edge_enabled = [True, True, True, True]
    source_vertex_id = 1

    graph = gp.GraphProcessor(vertex_ids, edge_ids, edge_vertex_id_pairs, edge_enabled, source_vertex_id)

    # Test edge 1 (1-2) - downstream should be 2,3,4,5
    assert sorted(graph.find_downstream_vertices(1)) == [2, 3, 4, 5]

    # Test edge 2 (2-3) - downstream should be 3
    assert graph.find_downstream_vertices(2) == [3]

    # Test edge 3 (2-4) - downstream should be 4,5
    assert sorted(graph.find_downstream_vertices(3)) == [4, 5]

    # Test edge 4 (4-5) - downstream should be 5
    assert graph.find_downstream_vertices(4) == [5]


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

    graph = gp.GraphProcessor(vertex_ids, edge_ids, edge_vertex_id_pairs, edge_enabled, source_vertex_id)

    # Source node 0
    assert sorted(graph.find_downstream_vertices(1)) == [2, 10]
    assert graph.find_downstream_vertices(9) == [10]
    assert graph.find_downstream_vertices(7) == []

    # Invalid edge_id
    with pytest.raises(gp.IDNotFoundError) as output:
        graph.find_downstream_vertices(2)
        assert output.value.args[0] == "The provided ID is not in the edge_ids list."

    # Source node 10
    graph.source_vertex_id = 10
    assert sorted(graph.find_downstream_vertices(9)) == [0, 2, 4, 6]


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

    test = gp.GraphProcessor(vertex_ids, edge_ids, edge_vertex_id_pairs, edge_enabled, source_vertex_id)

    # Test if edge 1 is correctly disabled
    gp.set_edge_enabled_status(test, 1, False)
    assert test.is_edge_enabled(1) == False

    # Test if error is raised if chosen edge is already disabled
    with pytest.raises(gp.EdgeAlreadyDisabledError) as output:
        gp.set_edge_enabled_status(test, 7, False)
        assert output.value.args[0] == "The chosen edge 7 is already disabled."

    # Test if error is raised if chosen edge is not a valid ID
    with pytest.raises(gp.IDNotFoundError) as output:
        gp.set_edge_enabled_status(test, 10, False)
        assert output.value.args[0] == "The chosen edge 10 is not in the ID list."

    # Test if edge 7 is actually enabled
    gp.set_edge_enabled_status(test, 7, True)
    assert test.is_edge_enabled(7) == True


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

    test = gp.GraphProcessor(vertex_ids, edge_ids, edge_vertex_id_pairs, edge_enabled, source_vertex_id)

    # tests if found alternative edges for disabled edge input are correct (connect the graph and acyclic)
    assert test.find_alternative_edges(1) == [7]
    assert test.find_alternative_edges(3) == [7, 8]
    assert test.find_alternative_edges(5) == [8]
    assert test.find_alternative_edges(9) == []

    # Test if error is raised if chosen edge is already disabled
    with pytest.raises(gp.EdgeAlreadyDisabledError) as output:
        test.find_alternative_edges(7)
        assert output.value.args[0] == "The chosen edge 7 is already disabled."

    # Test if error is raised if chosen edge is not a valid ID
    with pytest.raises(gp.IDNotFoundError) as output:
        test.find_alternative_edges(10)
        assert output.value.args[0] == "The chosen edge 10 is not in the ID list."
