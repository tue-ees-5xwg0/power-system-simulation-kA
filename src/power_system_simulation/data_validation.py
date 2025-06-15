"""
This module contains all the functions used for validating the PGM input data after its imported.
"""

from typing import Dict, List

import networkx as nx
import numpy as np

from power_system_simulation.exceptions import IDNotFoundError


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
