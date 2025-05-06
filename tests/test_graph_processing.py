from contextlib import nullcontext as does_not_raise
import power_system_simulation.graph_processing as gp
import pytest



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
    edge_vertex_id_pairs = [(1,2), (2,3), (2,4), (4,5), (4,6), (6,7), (7,8)]
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
    edge_vertex_id_pairs = [(1,2), (2,3), (2,4), (4,4), (4,6), (6,7), (7,8)]
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
    edge_vertex_id_pairs = [(1,2), (2,3), (2,4), (4,5), (4,6), (6,7), (7,8)]
    edge_enabled = [True, True, True, True, True, True, True]
    source_vertex_id = 1
    

    with pytest.raises(gp.IDNotUniqueError) as output:
        gp.GraphProcessor(vertex_ids, edge_ids, edge_vertex_id_pairs, edge_enabled, source_vertex_id)
    assert output.value.args[0] == "Input list edge_ids contains a duplicate at index 4 and 5." 



def test_graph_processor_init_err2_1():
    
    """
    One of the edges has no edge_vertex_id_pair and thus should result in a length mismatch error.
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
    edge_vertex_id_pairs = [(1,2), (2,4), (4,5), (4,6), (6,7), (7,8)]
    edge_enabled = [True, True, True, True, True, True, True]
    source_vertex_id = 1


    with pytest.raises(gp.InputLengthDoesNotMatchError) as output:
        gp.GraphProcessor(vertex_ids, edge_ids, edge_vertex_id_pairs, edge_enabled, source_vertex_id)
    assert output.value.args[0] == "The length of edge_ids does not match the length of edge_vertex_id_pairs." 



