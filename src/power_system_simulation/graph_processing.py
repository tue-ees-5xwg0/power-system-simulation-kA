"""
This is a skeleton for the graph processing assignment.

We define a graph processor class with some function skeletons.
"""

from typing import List, Tuple

import networkx as nx


class IDNotFoundError(Exception):
    pass


class InputLengthDoesNotMatchError(Exception):
    pass


class IDNotUniqueError(Exception):
    pass


class GraphNotFullyConnectedError(Exception):
    pass


class GraphCycleError(Exception):
    pass


class EdgeAlreadyDisabledError(Exception):
    pass


class GraphProcessor:
    """
    General documentation of this class.
    You need to describe the purpose of this class and the functions in it.
    We are using an undirected graph in the processor.
    """

    def __init__(
        self,
        vertex_ids: List[int],
        edge_ids: List[int],
        edge_vertex_id_pairs: List[Tuple[int, int]],
        edge_enabled: List[bool],
        source_vertex_id: int,
    ) -> None:
        """
        Initialize a graph processor object with an undirected graph.
        Only the edges which are enabled are taken into account.
        Check if the input is valid and raise exceptions if not.
        The following conditions should be checked:
            1. vertex_ids and edge_ids should be unique. (IDNotUniqueError)
            2. edge_vertex_id_pairs should have the same length as edge_ids. (InputLengthDoesNotMatchError)
            3. edge_vertex_id_pairs should contain valid vertex ids. (IDNotFoundError)
            4. edge_enabled should have the same length as edge_ids. (InputLengthDoesNotMatchError)
            5. source_vertex_id should be a valid vertex id. (IDNotFoundError)
            6. The graph should be fully connected. (GraphNotFullyConnectedError)
            7. The graph should not contain cycles. (GraphCycleError)
        If one certain condition is not satisfied, the error in the parentheses should be raised.

        Args:
            vertex_ids: list of vertex ids
            edge_ids: list of edge ids
            edge_vertex_id_pairs: list of tuples of two integer
                Each tuple is a vertex id pair of the edge.
            edge_enabled: list of bools indicating of an edge is enabled or not
            source_vertex_id: vertex id of the source in the graph
        """
        # put your implementation here

        # 1 check vertex_ids and edge_ids to be unique
        for id_origin in range(len(vertex_ids)):
            for id_check in range(len(vertex_ids)):
                if id_origin != id_check and vertex_ids[id_origin] == vertex_ids[id_check]:
                    raise IDNotUniqueError(
                        "Input list vertex_ids contains a duplicate at index %d and %d." % (id_origin, id_check)
                    )

        for id_origin in range(len(edge_ids)):
            for id_check in range(len(edge_ids)):
                if id_origin != id_check and edge_ids[id_origin] == edge_ids[id_check]:
                    raise IDNotUniqueError(
                        "Input list edge_ids contains a duplicate at index %d and %d." % (id_origin, id_check)
                    )

        # 2 check edge_vertex_id_pairs is the same length as edge_ids
        if len(edge_vertex_id_pairs) != len(edge_ids):
            raise InputLengthDoesNotMatchError(
                "The length of edge_ids does not match the length of edge_vertex_id_pairs."
            )

        # 3 check edge_vertex_id_pairs has valid vertex ids
        for pair in edge_vertex_id_pairs:
            for vertex_origin in pair:
                check = False
                for vertex_check in vertex_ids:
                    if vertex_origin == vertex_check:
                        check = True
                if not check:
                    raise IDNotFoundError("edge_vertex_id_pairs contains a non-existent vertex ID %d" % (vertex_origin))

        # 4 check edge_enabled has the same length as edge_ids
        if len(edge_enabled) != len(edge_ids):
            raise InputLengthDoesNotMatchError("The length of edge_ids does not match the length of edge_enabled.")

        # 5 source_vertex_id should be a valid vertex id
        check = False
        for vertex_check in vertex_ids:
            if vertex_check == source_vertex_id:
                check = True
        if not check:
            raise IDNotFoundError("The source_vertex_id %d is a non-existent vertex ID." % (source_vertex_id))

        # 6 the graph should be fully connected

        # 7 the graph should not contain cycles

        # self.vertex_ids = vertex_ids
        # self.edge_ids = edge_ids
        # self.edge_vertex_id_pairs = edge_vertex_id_pairs
        # self.edge_enabled = edge_enabled
        # self.source_vertex_id = source_vertex_id

    def find_downstream_vertices(self, edge_id: int) -> List[int]:
        """
        Given an edge id, return all the vertices which are in the downstream of the edge,
            with respect to the source vertex.
            Including the downstream vertex of the edge itself!

        Only enabled edges should be taken into account in the analysis.
        If the given edge_id is a disabled edge, it should return empty list.
        If the given edge_id does not exist, it should raise IDNotFoundError.


        For example, given the following graph (all edges enabled):

            vertex_0 (source) --edge_1-- vertex_2 --edge_3-- vertex_4

        Call find_downstream_vertices with edge_id=1 will return [2, 4]
        Call find_downstream_vertices with edge_id=3 will return [4]

        Args:
            edge_id: edge id to be searched

        Returns:
            A list of all downstream vertices.
        """
        # put your implementation here
        pass

    def find_alternative_edges(self, disabled_edge_id: int) -> List[int]:
        """
        Given an enabled edge, do the following analysis:
            If the edge is going to be disabled,
                which (currently disabled) edge can be enabled to ensure
                that the graph is again fully connected and acyclic?
            Return a list of all alternative edges.
        If the disabled_edge_id is not a valid edge id, it should raise IDNotFoundError.
        If the disabled_edge_id is already disabled, it should raise EdgeAlreadyDisabledError.
        If there are no alternative to make the graph fully connected again, it should return empty list.


        For example, given the following graph:

        vertex_0 (source) --edge_1(enabled)-- vertex_2 --edge_9(enabled)-- vertex_10
                 |                               |
                 |                           edge_7(disabled)
                 |                               |
                 -----------edge_3(enabled)-- vertex_4
                 |                               |
                 |                           edge_8(disabled)
                 |                               |
                 -----------edge_5(enabled)-- vertex_6

        Call find_alternative_edges with disabled_edge_id=1 will return [7]
        Call find_alternative_edges with disabled_edge_id=3 will return [7, 8]
        Call find_alternative_edges with disabled_edge_id=5 will return [8]
        Call find_alternative_edges with disabled_edge_id=9 will return []

        Args:
            disabled_edge_id: edge id (which is currently enabled) to be disabled

        Returns:
            A list of alternative edge ids.
        """
        # put your implementation here
        pass
