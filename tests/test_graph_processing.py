from contextlib import nullcontext as does_not_raise

import pytest

import power_system_simulation.graph_processing as gp


def test_graph_processor_init_normal():
    """
    Normal initialization of a graph processor, should result in no errors.
    1--[1]--2--[2]--3
            |
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

    assert gp.GraphProcessor(vertex_ids, edge_ids, edge_vertex_id_pairs, edge_enabled, source_vertex_id)


def test_graph_processor_init_err1_duplicate_vertex_ids():
    """
    Duplicate vertex ids.
    1--[1]--2--[2]--3
            |
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
    assert output.value.args[0] == "Input list vertex_ids contains a duplicate at index 3 and 4."


def test_graph_processor_init_err1_duplicate_edge_ids():
    """
    Duplicate edge ids.
    1--[1]--2--[2]--3
            |
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
    assert output.value.args[0] == "Input list edge_ids contains a duplicate at index 4 and 5."


def test_graph_processor_init_err2_id_pair_length_mismatch():
    """
    One of the edges has no edge_vertex_id_pair, or one too many id_pairs is entered and thus should result in a length mismatch error.
    1--[1]--2  [2]  3
            |
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


def test_graph_processor_init_err3_invalid_id_pair_id():
    """
    An ID pair is referring to a non-existent vertex.
    1--[1]--2--[2]--3
            |
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
    assert output.value.args[0] == "edge_vertex_id_pairs contains a non-existent vertex ID 9."


def test_graph_processor_init_err4_edge_enabled_length_mismatch():
    """
    The edge_enabled list contains too many or few entries, and should thus return a length mismatch error.
    1--[1]--2--[2]--3
            |
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


def test_graph_processor_init_err5_invalid_source_id():
    """
    The source ID is invalid.
    1--[1]--2--[2]--3
            |
    (9)    [3]
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
    source_vertex_id = 9

    with pytest.raises(gp.IDNotFoundError) as output:
        gp.GraphProcessor(vertex_ids, edge_ids, edge_vertex_id_pairs, edge_enabled, source_vertex_id)
    assert output.value.args[0] == "The source_vertex_id 9 is not in the ID list."


def test_graph_processor_init_err6_graph_not_connected_error():
    """
    The source ID is invalid.
    1--[1]--2--[2]--3
            |
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


def test_graph_processor_init_err6_graph_not_connected_disabled_error():
    """
    The source ID is invalid.
    1--[1]--2--[2]--3
            |
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


def test_graph_processor_init_err7_graph_contains_cycle_error():
    """
    The source ID is invalid.
    1--[1]--2--[2]--3
            |
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


def test_graph_processor_init_err7_graph_contains_cycle_disabled_error():
    """
    The source ID is invalid.
    1--[1]--2--[2]--3
            |
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

    assert gp.GraphProcessor(vertex_ids, edge_ids, edge_vertex_id_pairs, edge_enabled, source_vertex_id)


def test_is_edge_enabled():
    """
    The chosen edge is either enabled or disabled, or not a valid edge_id.

    vertex_0 (source) --edge_1(enabled)-- vertex_2 --edge_9(enabled)-- vertex_10
                 |                               |
                 |                           edge_7(disabled)
                 |                               |
                 -----------edge_3(enabled)-- vertex_4
                 |                               |
                 |                           edge_8(disabled)
                 |                               |
                 -----------edge_5(enabled)-- vertex_6
    """

    vertex_ids = [0, 2, 4, 6, 10]
    edge_ids = [1, 3, 5, 7, 8, 9]
    edge_vertex_id_pairs = [(0, 2), (0, 4), (0, 6), (2, 4), (4, 6), (2, 10)]
    edge_enabled = [True, True, True, False, False, True]
    source_vertex_id = 0

    test = gp.GraphProcessor(vertex_ids, edge_ids, edge_vertex_id_pairs, edge_enabled, source_vertex_id)
    assert gp.is_edge_enabled(test, 3) == True
    assert gp.is_edge_enabled(test, 7) == False

    with pytest.raises(gp.IDNotFoundError) as output:
        gp.is_edge_enabled(test, 10)
    assert output.value.args[0] == "The chosen edge 10 is not in the ID list."


def test_edge_set_to_correct_enabled_status():
    """
    Tests that the edge is correctly set to enabled or disabled
    and if error is given is edge is already disabled or not a valid id.

    vertex_0 (source) --edge_1(enabled)-- vertex_2 --edge_9(enabled)-- vertex_10
                 |                               |
                 |                           edge_7(disabled)
                 |                               |
                 -----------edge_3(enabled)-- vertex_4
                 |                               |
                 |                           edge_8(disabled)
                 |                               |
                 -----------edge_5(enabled)-- vertex_6
    """

    vertex_ids = [0, 2, 4, 6, 10]
    edge_ids = [1, 3, 5, 7, 8, 9]
    edge_vertex_id_pairs = [(0, 2), (0, 4), (0, 6), (2, 4), (4, 6), (2, 10)]
    edge_enabled = [True, True, True, False, False, True]
    source_vertex_id = 0

    test = gp.GraphProcessor(vertex_ids, edge_ids, edge_vertex_id_pairs, edge_enabled, source_vertex_id)
    gp.set_edge_enabled_status(test, 1, False)
    assert gp.is_edge_enabled(test, 1) == False  # Test if edge 1 is actually disabled

    with pytest.raises(gp.EdgeAlreadyDisabledError) as output:
        gp.set_edge_enabled_status(test, 7, False)
    assert output.value.args[0] == "The chosen edge 7 is already disabled."

    with pytest.raises(gp.IDNotFoundError) as output:
        gp.set_edge_enabled_status(test, 10, False)
    assert output.value.args[0] == "The chosen edge 10 is not in the ID list."

    gp.set_edge_enabled_status(test, 7, True)
    assert gp.is_edge_enabled(test, 7) == True  # Test if edge 7 is actually enabled


# def test_find_downstream_vertices_err1():
#     """
#     Placeholder test with a normal network. Should be turned into an actual test when the function has been made.
#     1--[1]--2--[2]--3
#             |
#            [3]
#             |
#             4--[4]--5
#             |
#            [5]
#             |
#             6--[6]--7--[7]--8
#     """

#     vertex_ids = [1, 2, 3, 4, 5, 6, 7, 8]
#     edge_ids = [1, 2, 3, 4, 5, 6, 7]
#     edge_vertex_id_pairs = [(1, 2), (2, 3), (2, 4), (4, 5), (4, 6), (6, 7), (7, 8)]
#     edge_enabled = [True, True, True, True, True, True, True]
#     source_vertex_id = 1

#     test = gp.GraphProcessor(vertex_ids, edge_ids, edge_vertex_id_pairs, edge_enabled, source_vertex_id)
#     assert test.find_downstream_vertices(1) == None


def test_find_alternative_edges_err1():
    """
    Tests that alternative edges are found

    vertex_0 (source) --edge_1(enabled)-- vertex_2 --edge_9(enabled)-- vertex_10
                 |                               |
                 |                           edge_7(disabled)
                 |                               |
                 -----------edge_3(enabled)-- vertex_4
                 |                               |
                 |                           edge_8(disabled)
                 |                               |
                 -----------edge_5(enabled)-- vertex_6
    """
    vertex_ids = [0, 2, 4, 6, 10]
    edge_ids = [1, 3, 5, 7, 8, 9]
    edge_vertex_id_pairs = [(0, 2), (0, 4), (0, 6), (2, 4), (4, 6), (2, 10)]
    edge_enabled = [True, True, True, False, False, True]
    source_vertex_id = 0

    test = gp.GraphProcessor(vertex_ids, edge_ids, edge_vertex_id_pairs, edge_enabled, source_vertex_id)
    assert test.find_alternative_edges(1) == [7]
    assert test.find_alternative_edges(3) == [7, 8]
    assert test.find_alternative_edges(5) == [8]
    assert test.find_alternative_edges(9) == []

    with pytest.raises(gp.EdgeAlreadyDisabledError) as output:
        test.find_alternative_edges(7)
    assert output.value.args[0] == "The chosen edge 7 is already disabled."

    with pytest.raises(gp.IDNotFoundError) as output:
        test.find_alternative_edges(10)
    assert output.value.args[0] == "The chosen edge 10 is not in the ID list."
