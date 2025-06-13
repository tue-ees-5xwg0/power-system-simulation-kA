"""
This is a file containing the GraphProcessor object class to process the power grid and supplemental functions.
"""

import copy
from typing import List, Tuple, Dict

import networkx as nx

from power_system_simulation.data_validation import *
from power_system_simulation.exceptions import *


def create_graph(
    nodes: List[Dict],
    lines: List[Dict],
    sym_loads: List[Dict],
    source_node: Dict
) -> nx.Graph:
    if has_duplicate_ids(nodes, lines, sym_loads, source_node):
        raise IDNotUniqueError("There are components with duplicate IDs.")
    if not has_node_ids(nodes, lines):
        raise IDNotFoundError("Line(s) contain(s) non-existent node ID.")
    if not has_node_ids(nodes, sym_loads):
        raise IDNotFoundError("Sym_load(s) contain(s) non-existent node ID.")
    if not has_source_id(nodes, source_node[0]["node"]):
        raise IDNotFoundError("The provided source_node is not in the node list.")

    G = nx.Graph()

    for node in nodes:
        G.add_node(node["id"], type="node", u_rated=node["u_rated"])

    for line in lines:
        G.add_edge(line["from_node"], line["to_node"], id=line["id"], from_status=line["from_status"], to_status=line["to_status"])
    
    for sym_load in sym_loads:
        G.add_node(sym_load["id"], type="sym_load")
        G.add_edge(sym_load["id"], sym_load["node"])

    G.graph["source_node"] = source_node[0]["node"]
    
    filtered = filter_disabled_edges(G)
    if not nx.is_connected(filtered):
        raise GraphNotFullyConnectedError("The graph is not fully connected.")
    if is_cyclic(filtered):
        raise GraphCycleError("The graph contains a cycle.")

    return G


def filter_disabled_edges(graph):
    enabled_edges = [(u, v, d) for u, v, d in graph.edges(data=True) if (d.get("from_status") != 0 and d.get("to_status") != 0) is True]
    G = nx.Graph()
    G.add_nodes_from(graph.nodes)
    G.graph["source_node"] = graph.graph["source_node"]
    for u, v, d in enabled_edges:
        G.add_edge(u, v, **d)
    return G


def set_edge_enabled_status(graph: nx.Graph, edge_id: int, status: bool):
    for u, v, d in graph.edges(data=True):
        if d.get("id") == edge_id:
            if (d.get("enabled") == status) and (status is False):
                raise EdgeAlreadyDisabledError(f"The chosen edge {edge_id} is already disabled.")
            graph[u][v]["enabled"] = status
            return
    raise IDNotFoundError(f"The chosen edge {edge_id} is not in the ID list.")


def is_edge_enabled(graph: nx.Graph, edge_id: int) -> bool:
    for _, _, d in graph.edges(data=True):
        if d.get("id") == edge_id:
            return (d.get("to_status", False) and d.get("to_status", False))
    raise IDNotFoundError(f"The chosen edge {edge_id} is not in the ID list.")


def is_cyclic(graph: nx.Graph) -> bool:
    try:
        nx.find_cycle(graph)
        return True
    except nx.NetworkXNoCycle:
        return False


def find_downstream_vertices(graph: nx.Graph, edge_id: int) -> List[int]:
    edge_ids = [line.get("id") for _, _, line in graph.edges(data=True)]
    if not has_source_id(edge_ids, edge_id):
        raise IDNotFoundError("The provided ID is not in the edge_ids list.")

    edge_data = None
    edge_vertices = None
    for u, v, data in graph.edges(data=True):
        if data.get("id") == edge_id:
            edge_data = data
            edge_vertices = (u, v)
            break

    if not edge_data.get("enabled", False):
        return []

    filtered_graph = filter_disabled_edges(graph)
    try:
        bfs_tree = nx.bfs_tree(filtered_graph, graph.graph["source_node"])
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


def find_alternative_edges(graph: nx.Graph, disabled_edge_id: int) -> List[int]:
    graph_copy = copy.deepcopy(graph)
    set_edge_enabled_status(graph_copy, disabled_edge_id, False)

    valid_alternatives = []

    # find currently disabled edges
    for u, v, d in graph.edges(data=True):
        if not d.get("enabled", None):
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
