"""
This module contains all the functions used for validating the PGM input data after its imported.
"""

from typing import Dict, List

import networkx as nx
import numpy as np

from power_system_simulation.exceptions import IDNotFoundError, IDNotUniqueError


def has_duplicate_ids(*args: np.ndarray):
    """
    Checks for duplicate ids in power_grid component lists.
    """
    ids = []
    for ls in args:
        for item in ls:
            ids.append(item["id"])

    return len(ids) != len(set(ids))


def has_node_ids(nodes: List[Dict], lines: List[Dict]):
    """
    Checks if the list refers to existing nodes, works for lines, transformers, sym_loads an source nodes.
    """
    node_ids = []
    for node in nodes:
        node_ids.append(node["id"])
    try:
        for line in lines:
            if (line["from_node"] not in node_ids) or (line["to_node"] not in node_ids):
                return False
    except:
        try:
            for line in lines:
                if line["node"] not in node_ids:
                    return False
        except:
            raise TypeError("Datatype not supported by this function")

    return True


def is_edge_enabled(graph: nx.Graph, edge_id: int) -> bool:
    """
    Checks if an edge in a graph is enabled or not.
    """
    for _, _, d in graph.edges(data=True):
        if d.get("id") == edge_id:
            return d.get("to_status", False) and d.get("to_status", False)
    raise IDNotFoundError(f"The provided edge {edge_id} is not in the ID list.")


def validate_power_grid_data(power_grid):
    """
    Used to validate the PGM input data for duplicate ids and invalid references.
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
