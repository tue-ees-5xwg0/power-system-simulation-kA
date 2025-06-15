"""
This module contains all exceptions raised by the power_system_simulation package.
"""


class NoValidOutputDataError(Exception):
    """Raised when there is no output from the power_grid_model to work with."""


class LoadProfileMismatchError(Exception):
    """Raised when the active and reactive load profiles do not align."""


class ValidationError(Exception):
    """Raised when invalid data is attempted to be used."""


class DataNotFoundError(Exception):
    """Raised when no data is found in a variable."""


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
