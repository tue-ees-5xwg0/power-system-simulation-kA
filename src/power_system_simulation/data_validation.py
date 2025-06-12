from typing import List, Tuple

import networkx as nx

from power_system_simulation.exceptions import *


def has_duplicate_ids(ids: List[int]):
    return len(ids) != len(set(ids))


def has_same_length(list1, list2):
    return len(list1) == len(list2)


def has_vertex_ids(vertex_ids: List[int], edge_vertex_id_pairs: List[Tuple[int, int]]):
    return all(u in vertex_ids and v in vertex_ids for u, v in edge_vertex_id_pairs)


def has_id(ids: List[int], id_check: int):
    return id_check in ids
