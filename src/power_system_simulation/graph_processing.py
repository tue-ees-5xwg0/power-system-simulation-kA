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


def check_duplicate_ids(ids: List[int], list_name):
    "Check for duplicate ids in a list that should have unique ids"
    for i_origin, id_origin in enumerate(ids):
        for i_check, id_check in enumerate(ids):
            if i_origin != i_check and id_origin == id_check:
                raise IDNotUniqueError(
                    f"Input list {list_name} contains a duplicate at index {i_origin} and {i_check}."
                )


def check_same_length(list1, list2, list1_name, list2_name):
    "Check if two lists have the same length. This is useful when one list maps to the entries in another list."
    if len(list1) != len(list2):
        raise InputLengthDoesNotMatchError(f"The length of {list1_name} does not match the length of {list2_name}.")


def check_contains_vertex_ids(vertex_ids: List[int], edge_vertex_id_pairs: List[Tuple[int, int]]):
    "Check if all vertex_ids int the edge_vertex_id_pairs list map to an existing vertex_id."
    for pair in edge_vertex_id_pairs:
        for vertex_origin in pair:
            check = False
            for vertex_check in vertex_ids:
                if vertex_origin == vertex_check:
                    check = True
            if not check:
                raise IDNotFoundError(f"edge_vertex_id_pairs contains a non-existent vertex ID {vertex_origin}.")


def check_contains_id(ids: List[int], id_check: int, item_name):
    "Checks if a specific ID is present in a list."
    for id_origin in ids:
        if id_origin == id_check:
            return
    raise IDNotFoundError(f"The {item_name} {id_check} is not in the ID list.")


class GraphProcessor(nx.Graph):
    """
    This class is an extension of the NetworkX undirected graph. It functions as a processor for network graphs.
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
        check_duplicate_ids(vertex_ids, "vertex_ids")
        check_duplicate_ids(edge_ids, "edge_ids")

        # 2 check edge_vertex_id_pairs is the same length as edge_ids
        check_same_length(edge_ids, edge_vertex_id_pairs, "edge_ids", "edge_vertex_id_pairs")

        # 3 check edge_vertex_id_pairs has valid vertex ids
        check_contains_vertex_ids(vertex_ids, edge_vertex_id_pairs)

        # 4 check edge_enabled has the same length as edge_ids
        check_same_length(edge_ids, edge_enabled, "edge_ids", "edge_enabled")

        # 5 source_vertex_id should be a valid vertex id
        check_contains_id(vertex_ids, source_vertex_id, "source_vertex_id")

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
