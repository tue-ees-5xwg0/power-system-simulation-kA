"""
This is a skeleton for the graph processing assignment.

We define a graph processor class with some function skeletons.
"""

from typing import List, Tuple

import networkx as nx


class IDNotFoundError(Exception):
    "Error when an ID in a list cannot be found."


class InputLengthDoesNotMatchError(Exception):
    "Error when 2 lists are not of the same length."


class IDNotUniqueError(Exception):
    "Error when there is a duplicate ID in an ID list."


class GraphNotFullyConnectedError(Exception):
    "Error when a graph is split and thus not fully connected to the source vertex."


class GraphCycleError(Exception):
    "Error when a graph has a loop in it. This is not allowed."


class EdgeAlreadyDisabledError(Exception):
    "Error when trying to disable an edge that is already disabled."


class GraphProcessor(nx.Graph):
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

        # initialize the nx.Graph base object
        super().__init__()

        # 1 check vertex_ids and edge_ids to be unique
        for i_origin, id_origin in enumerate(vertex_ids):
            for i_check, id_check in enumerate(vertex_ids):
                if i_origin != i_check and id_origin == id_check:
                    raise IDNotUniqueError(
                        f"Input list vertex_ids contains a duplicate at index {i_origin} and {i_check}."
                    )

        for i_origin, id_origin in enumerate(edge_ids):
            for i_check, id_check in enumerate(edge_ids):
                if i_origin != i_check and id_origin == id_check:
                    raise IDNotUniqueError(
                        f"Input list edge_ids contains a duplicate at index {i_origin} and {i_check}."
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
                    raise IDNotFoundError(f"edge_vertex_id_pairs contains a non-existent vertex ID {vertex_origin}.")

        # 4 check edge_enabled has the same length as edge_ids
        if len(edge_enabled) != len(edge_ids):
            raise InputLengthDoesNotMatchError("The length of edge_ids does not match the length of edge_enabled.")

        # 5 source_vertex_id should be a valid vertex id
        check = False
        for vertex_check in vertex_ids:
            if vertex_check == source_vertex_id:
                check = True
        if not check:
            raise IDNotFoundError(f"The source_vertex_id {source_vertex_id} is a non-existent vertex ID.")

        # create nx graph after input checks
        self.add_nodes_from(vertex_ids)
        for i, (u, v) in enumerate(edge_vertex_id_pairs):
            self.add_edge(u, v, id=edge_ids[i], enabled=edge_enabled[i])
        self.source_vertex_id = source_vertex_id

        # 6 the graph should be fully connected


        # 7 the graph should not contain cycles


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

    def find_alternative_edges(self, disabled_edge_id: int) -> List[int]:
        a = 2
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
