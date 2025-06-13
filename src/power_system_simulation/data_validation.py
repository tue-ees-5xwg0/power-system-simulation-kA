from typing import List, Tuple, Dict

import networkx as nx

from power_system_simulation.exceptions import *


def has_duplicate_ids(*args: List[int]):
    
    ids = []
    for list in args:
        for item in list:
            ids.append(item["id"])
    
    return len(ids) != len(set(ids))


# def has_same_length(list1, list2):
#     return len(list1) == len(list2)


def has_node_ids(nodes: List[Dict], lines :List[Dict]):
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


def has_source_id(nodes: List[Dict], id_check: int):
    node_ids = []
    for node in nodes:
        node_ids.append(node["id"])
    return id_check in node_ids


def has_edge_id(edges: List[int], id_check: int):
    
    return id_check in edges


def is_edge_enabled(graph: nx.Graph, edge_id: int) -> bool:
    for _, _, d in graph.edges(data=True):
        if d.get("id") == edge_id:
            return (d.get("to_status", False) and d.get("to_status", False))
    raise IDNotFoundError(f"The chosen edge {edge_id} is not in the ID list.")