"""
This is a file containing the GraphProcessor object class to process the power grid and supplemental functions.
"""

import copy
from typing import List

import networkx as nx

from power_system_simulation.data_validation import has_duplicate_ids, has_node_ids, is_edge_enabled
from power_system_simulation.exceptions import (
    EdgeAlreadyDisabledError,
    GraphCycleError,
    GraphNotFullyConnectedError,
    IDNotFoundError,
    IDNotUniqueError,
)


def create_graph(power_grid) -> nx.Graph:
    """
    This function is used to create a graph object from the NetworkX package which can be used to run checks and
    edits on the griddata. Input data should be in PGM format from the power-grid-model package. It should
    contain node, lines, sym_loads and exactly one transformer and source node.
    """

    nodes = power_grid["node"]
    lines = power_grid["line"]
    source = power_grid["source"]
    sym_loads = power_grid["sym_load"]
    transformer = power_grid["transformer"]

    if has_duplicate_ids(nodes, lines, source, sym_loads, transformer):
        raise IDNotUniqueError("There are components with duplicate IDs.")
    if not has_node_ids(nodes, lines):
        raise IDNotFoundError("Line(s) contain(s) non-existent node ID.")
    if not has_node_ids(nodes, sym_loads):
        raise IDNotFoundError("Sym_load(s) contain(s) non-existent node ID.")
    if not has_node_ids(nodes, transformer):
        raise IDNotFoundError("Transformer contains non-existent node ID.")
    if not has_node_ids(nodes, source):
        raise IDNotFoundError("The provided source_node_id is not in the node list.")

    graph = nx.Graph()

    for node in nodes:
        graph.add_node(node["id"], type="node", u_rated=node["u_rated"])

    graph.add_edge(
        transformer["from_node"][0],
        transformer["to_node"][0],
        id=transformer["id"][0],
        type="transformer",
        from_status=transformer["from_status"][0],
        to_status=transformer["to_status"][0],
    )

    for line in lines:
        graph.add_edge(
            line["from_node"],
            line["to_node"],
            id=line["id"],
            type="line",
            from_status=line["from_status"],
            to_status=line["to_status"],
        )

    for sym_load in sym_loads:
        graph.add_node(sym_load["id"], type="sym_load")
        graph.add_edge(sym_load["id"], sym_load["node"], type="sym_load")

    graph.graph["source_node_id"] = source[0]["node"]

    filtered = filter_disabled_edges(graph)
    if not nx.is_connected(filtered):
        raise GraphNotFullyConnectedError("The graph is not fully connected.")
    if is_cyclic(filtered):
        raise GraphCycleError("The graph contains a cycle.")

    return graph


def filter_disabled_edges(graph, remove_sym_loads=False):
    """
    Returns a copy of a graph without the disabled edges, for easy processing. It also has the option to (disabled by
    default) return a copy without any sym_loads too.
    """

    filtered = nx.Graph()

    if remove_sym_loads:
        enabled_edges = [
            (u, v, d)
            for u, v, d in graph.edges(data=True)
            if (d.get("from_status") != 0 and d.get("to_status") != 0) and (d.get("type") != "sym_load")
        ]
        enabled_nodes = [(n, d) for n, d in graph.nodes(data=True) if d.get("type") != "sym_load"]
    else:
        enabled_edges = [
            (u, v, d) for u, v, d in graph.edges(data=True) if (d.get("from_status") != 0 and d.get("to_status") != 0)
        ]
        enabled_nodes = graph.nodes

    filtered.add_nodes_from(enabled_nodes)
    filtered.add_edges_from(enabled_edges)

    filtered.graph["source_node_id"] = graph.graph["source_node_id"]
    return filtered


def set_edge_enabled_status(graph: nx.Graph, edge_id: int, status: bool):
    """
    Sets the status of an edge to enabled or disabled. If already disabled, it will raise an EdgeAlreadyDisabledError.
    """

    for u, v, d in graph.edges(data=True):
        if d.get("id") == edge_id:
            if (d.get("from_status") == 0 or d.get("to_status") == 0) and (status is False):
                raise EdgeAlreadyDisabledError(f"The chosen edge {edge_id} is already disabled.")

            if status is False:
                graph[u][v]["from_status"] = 0
                graph[u][v]["to_status"] = 0

            else:
                graph[u][v]["from_status"] = 1
                graph[u][v]["to_status"] = 1

            return
    raise IDNotFoundError(f"The chosen edge {edge_id} is not in the ID list.")


def is_cyclic(graph: nx.Graph) -> bool:
    """
    Checks if a graph has a cycle in it. This also includes the disabled edges.
    """
    try:
        nx.find_cycle(graph)
        return True
    except nx.NetworkXNoCycle:
        return False


def find_downstream_vertices(graph: nx.Graph, edge_id: int) -> List[int]:
    """
    Returns all nodes downstream of the provided edge, with respect to the graphs' source node
    """

    edge_vertices = None

    if not is_edge_enabled(graph, edge_id):
        return []

    for u, v, data in graph.edges(data=True):
        if data.get("id") == edge_id:
            edge_vertices = (u, v)
            break

    filtered_graph = filter_disabled_edges(graph, True)
    try:
        bfs_tree = nx.bfs_tree(filtered_graph, graph.graph["source_node_id"])

    except:
        raise IDNotFoundError("source_node_id is non-existent.")

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


def find_alternative_edges(graph: nx.Graph, disabled_edge_id: int) -> List[int]:
    """
    Returns all alternative edges that could be enabled to make the graph connected, after disabling the provided edge.
    """

    graph_copy = copy.deepcopy(graph)
    set_edge_enabled_status(graph_copy, disabled_edge_id, False)

    valid_alternatives = []

    # find currently disabled edges
    for _, _, d in graph.edges(data=True):
        if d.get("type") != "sym_load" and (d.get("from_status", None) == 0 or d.get("to_status", None) == 0):
            candidate_edge_id = d.get("id", None)

            # enable originally disabled edge
            test_graph = copy.deepcopy(graph_copy)
            set_edge_enabled_status(test_graph, candidate_edge_id, True)

            # check per if whole graph is accesible
            # Since the graph is acyclic from the start, it will stay acyclic when enabling only one edge.
            if not nx.is_connected(filter_disabled_edges(test_graph)):
                continue
                # raise GraphNotFullyConnectedError("The graph is not fully connected.")
            valid_alternatives.append(candidate_edge_id)

    return valid_alternatives
