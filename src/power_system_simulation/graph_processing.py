"""
This is a file containing the GraphProcessor object class, and supplemental functions.
"""

import copy
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


def filter_disabled_edges(graph):
    """
    Returs a GraphProcessor with all disabled edges removed.
    """

    vertex_ids = graph.nodes

    enabled_edges = [(u, v, d) for u, v, d in graph.edges(data=True) if d.get("enabled", None) is True]
    edge_ids = []
    edge_vertex_id_pairs = []
    edge_enabled = []

    for edge in enabled_edges:
        edge_ids.append(edge[2].get("id", None))
        edge_vertex_id_pairs.append((edge[0], edge[1]))
        edge_enabled.append(True)

    return GraphProcessor(vertex_ids, edge_ids, edge_vertex_id_pairs, edge_enabled, graph.source_vertex_id, True)


def set_edge_enabled_status(graph: nx.Graph, edge_id: int, status: bool):
    """
    Enables or disables an edge by its ID.
    Checks if the edge_id:
    - is valid
    - if it is already disabled (when prompted to be turned disabled).
    """

    for u, v, d in graph.edges(data=True):
        if d.get("id") == edge_id:
            if d.get("enabled", None) == status:
                if status is False:
                    raise EdgeAlreadyDisabledError(f"The chosen edge {edge_id} is already disabled.")
            graph[u][v]["enabled"] = status
            return
    raise IDNotFoundError(f"The chosen edge {edge_id} is not in the ID list.")


class GraphProcessor(nx.Graph):
    """
    This class is an extension of the NetworkX undirected graph. It functions as a processor for
    network graphs.
    """

    def __init__(
        self,
        vertex_ids: List[int],
        edge_ids: List[int],
        edge_vertex_id_pairs: List[Tuple[int, int]],
        edge_enabled: List[bool],
        source_vertex_id: int,
        recursive_object=False,
    ) -> None:

        # initialize the nx.Graph base object
        super().__init__()

        # 1 check vertex_ids and edge_ids to be unique
        if self._has_duplicate_ids(vertex_ids):
            raise IDNotUniqueError("Input list vertex_ids contains a duplicate id.")
        if self._has_duplicate_ids(edge_ids):
            raise IDNotUniqueError("Input list edge_ids contains a duplicate id.")

        # 2 check edge_vertex_id_pairs is the same length as edge_ids
        if not self._has_same_length(edge_ids, edge_vertex_id_pairs):
            raise InputLengthDoesNotMatchError(
                "The length of edge_ids does not match the length of edge_vertex_id_pairs."
            )

        # 3 check edge_vertex_id_pairs has valid vertex ids
        if not self._has_vertex_ids(vertex_ids, edge_vertex_id_pairs):
            raise IDNotFoundError("edge_vertex_id_pairs contains a non-existent vertex ID.")

        # 4 check edge_enabled has the same length as edge_ids
        if not self._has_same_length(edge_ids, edge_enabled):
            raise InputLengthDoesNotMatchError("The length of edge_ids does not match the length of edge_enabled.")

        # 5 source_vertex_id should be a valid vertex id
        if not self._has_id(vertex_ids, source_vertex_id):
            raise IDNotFoundError("The provided source_vertex_id is not in the vertex_ids list.")

        # create nx graph after input checks
        self.add_nodes_from(vertex_ids)
        for i, (u, v) in enumerate(edge_vertex_id_pairs):
            self.add_edge(u, v, id=edge_ids[i], enabled=edge_enabled[i])
        self.source_vertex_id = source_vertex_id

        # only run this if the object is created as a normal object, not when run by another function such as is_cyclic
        if not recursive_object:

            # 6 the graph should be fully connected
            if not nx.is_connected(filter_disabled_edges(self)):
                raise GraphNotFullyConnectedError("The graph is not fully connected.")

            # 7 the graph should not contain cycles
            if filter_disabled_edges(self).is_cyclic():
                raise GraphCycleError("The graph contains a cycle.")

    def _has_duplicate_ids(self, ids: List[int]):
        """
        Check for duplicate ids in a list that should have unique ids
        """

        for i_origin, id_origin in enumerate(ids):
            for i_check, id_check in enumerate(ids):
                if i_origin != i_check and id_origin == id_check:
                    return True
        return False

    def _has_same_length(self, list1, list2):
        """
        Check if two lists have the same length. This is useful when one list maps to the entries in another list.
        """

        if len(list1) != len(list2):
            return False
        return True

    def _has_vertex_ids(self, vertex_ids: List[int], edge_vertex_id_pairs: List[Tuple[int, int]]):
        """
        Check if all vertex_ids int the edge_vertex_id_pairs list map to an existing vertex_id.
        """

        for pair in edge_vertex_id_pairs:
            for vertex_origin in pair:
                check = False
                for vertex_check in vertex_ids:
                    if vertex_origin == vertex_check:
                        check = True
                if not check:
                    return False
        return True

    def _has_id(self, ids: List[int], id_check: int):
        """
        Checks if a specific ID is present in a list.
        """

        for id_origin in ids:
            if id_origin == id_check:
                return True
        return False

    def is_cyclic(self, orientation=None) -> bool:
        """
        Checks if the graph is cyclic. It also takes into account the disabled edges. If you want it to not take into
        account the disabled edges, create a duplicate graph object with the disabled edges filtered out of it. (You
        can use filter_disabled_edges(self) for that)
        """

        if not self.is_directed() or orientation in (None, "original"):

            def tailhead(edge):
                return edge[:2]

        explored = set()
        cycle = []
        for start_node in self.nbunch_iter(self.source_vertex_id):
            # if start_node in explored:
            #     # No loop is possible.
            #     continue

            edges = []
            # All nodes seen in this iteration of edge_dfs
            seen = {start_node}
            # Nodes in active path.
            active_nodes = {start_node}
            previous_head = None

            for edge in nx.edge_dfs(self, start_node, orientation):
                # Determine if this edge is a continuation of the active path.
                tail, head = tailhead(edge)

                # if head in explored:
                # Then we've already explored it. No loop is possible.
                # continue

                if previous_head is not None and tail != previous_head:
                    # This edge results from backtracking.
                    # Pop until we get a node whose head equals the current tail.
                    # So for example, we might have:
                    #  (0, 1), (1, 2), (2, 3), (1, 4)
                    # which must become:
                    #  (0, 1), (1, 4)
                    while True:
                        try:
                            popped_edge = edges.pop()
                        except IndexError:
                            edges = []
                            active_nodes = {tail}
                            break
                        else:
                            popped_head = tailhead(popped_edge)[1]
                            active_nodes.remove(popped_head)

                        if edges:
                            last_head = tailhead(edges[-1])[1]
                            if tail == last_head:
                                break
                edges.append(edge)

                if head in active_nodes:
                    # We have a loop!
                    cycle.extend(edges)
                    break

                seen.add(head)
                active_nodes.add(head)
                previous_head = head

            if cycle:
                break

            explored.update(seen)

        else:
            assert len(cycle) == 0
            return False

        return True

    def is_edge_enabled(self, edge_id: int) -> bool:
        """
        Checks if the edge is present in the list and if it is already disabled.
        """

        chosen_edge = [(u, v, d) for u, v, d in self.edges(data=True) if d.get("id") == edge_id]

        if not chosen_edge:
            raise IDNotFoundError(f"The chosen edge {edge_id} is not in the ID list.")

        enabled_status = chosen_edge[0][2].get("enabled", None)

        if enabled_status is False:
            return False

        return True

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

        edge_ids = [data.get("id") for _, _, data in self.edges(data=True)]
        if not self._has_id(edge_ids, edge_id):
            raise IDNotFoundError("The provided ID is not in the edge_ids list.")

        edge_data = None
        edge_vertices = None
        for u, v, data in self.edges(data=True):
            if data.get("id") == edge_id:
                edge_data = data
                edge_vertices = (u, v)
                break

        if not edge_data.get("enabled", False):
            return []

        filtered_graph = filter_disabled_edges(self)
        try:
            bfs_tree = nx.bfs_tree(filtered_graph, self.source_vertex_id)
        except nx.NetworkXError:
            return []

        u, v = edge_vertices
        if bfs_tree.has_edge(u, v):
            downstream_vertex = v
        elif bfs_tree.has_edge(v, u):
            downstream_vertex = u
        else:
            return []

        subtree_nodes = list(nx.descendants(bfs_tree, downstream_vertex))
        subtree_nodes.append(downstream_vertex)

        return sorted(subtree_nodes)

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

        # copy graph (which can be edited)
        # Set chosen edge to disabled -> Returns errors if edge is already disabled or not valid id
        self_copy = copy.deepcopy(self)
        set_edge_enabled_status(self_copy, disabled_edge_id, False)

        valid_alternatives = []

        # find currently disabled edges
        for u, v, d in self.edges(data=True):
            if not d.get("enabled", None):
                candidate_edge_id = d.get("id", None)

                # enable originally disabled edge
                test_graph = copy.deepcopy(self_copy)
                set_edge_enabled_status(test_graph, candidate_edge_id, True)

                # check per if whole graph is accesible
                # Since the graph is acyclic from the start, it will stay acyclic when enabling only one edge.
                if not nx.is_connected(filter_disabled_edges(test_graph)):
                    continue
                    # raise GraphNotFullyConnectedError("The graph is not fully connected.")
                valid_alternatives.append(candidate_edge_id)

        return valid_alternatives
