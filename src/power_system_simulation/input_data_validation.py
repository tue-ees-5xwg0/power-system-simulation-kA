"""
This module contains all the functions used for validating the PGM input data after its imported.
"""

from json import load
from typing import Dict, List, Optional

import networkx as nx
import numpy as np
import pandas as pd
from power_grid_model.utils import json_deserialize

from power_system_simulation.exceptions import (
    IDNotFoundError,
    IDNotUniqueError,
    LoadProfileMismatchError,
    ValidationError,
)


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


def has_valid_edges(*args: np.ndarray):
    for edges in args:
        for edge in edges:
            if edge["from_node"] == edge["to_node"]:
                return False
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

    if len(transformer) != 1:
        raise ValidationError(
            "Transformer list contains more that 1 transformer. Only 1 transformer is supported for this object."
        )
    if len(source) != 1:
        raise ValidationError("Source list contains more that 1 source. Only 1 source is supported for this object.")
    if not has_valid_edges(lines, transformer):
        raise IDNotUniqueError("An edge is connected to the same node on both sides.")
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


def validate_meta_data(power_grid, meta_data):

    # validate that the feeder IDs correspond to a line ID
    feeder_lines = []
    for feeder in meta_data["lv_feeders"]:
        found = False
        for line in power_grid["line"]:
            if line["id"] == feeder:
                feeder_lines.append(line)
                found = True
        if not found:
            raise ValidationError(f"Feeder ID {feeder} is a non-existend line ID.")

    # validate that all feeders have from_node equal to to_node of transformer (meta_data: lv_busbar)
    for feeder in feeder_lines:
        if feeder["from_node"] != power_grid["transformer"][0]["to_node"]:
            raise ValidationError(f"Feeder ID {feeder["id"]} not connected to the transformer output (LV_busbar.")


def validate_power_profiles_timestamps(profile1: pd.DataFrame, profile2: pd.DataFrame):
    if not profile1.index.equals(profile2.index):
        raise LoadProfileMismatchError("Timestamps do not match between power profiles.")


def validate_ev_charging_profile(power_grid, ev_charging_profile):
    if len(ev_charging_profile.columns) < len(power_grid.power_grid["sym_load"]):
        raise ValidationError(
            "ev_charging_profile does not contain enough nodes for this power_grid (less power profiles than sym_loads)."
        )


def load_grid_json(path):
    """
    Loads the power_grid from a specified .PGM file and validates it.
    """
    with open(path, "r", encoding="utf-8") as file:
        power_grid = json_deserialize(file.read())

    return power_grid


def load_meta_data_json(path):
    """
    Loads te metadata of a powergrid
    """

    with open(path, "r", encoding="utf-8") as file:
        meta_data = load(file)

    return meta_data
