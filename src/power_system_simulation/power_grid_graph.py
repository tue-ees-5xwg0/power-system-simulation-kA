from power_grid_model.utils import json_deserialize


class PowerGridGraph():
    """
    This class stores a power grid graph, this can then be used to create a PowerGridSimulation or a GraphProcessor.
    """

    def __init__(self, path=None):
        self.valid = False
        self.data = None

        if path is not None:
            self.load_json(path)

    def load_json(self, path):
        with open(path, "r", encoding="utf-8") as file:
            self.data = json_deserialize(file.read())

        self.valid = self._validate()

    def _validate(self):
        # TODO: implement validation checks
        self.valid = True

    def add_node(self):
        pass

    def remove_node(self):
        pass

    def add_line(self):
        pass

    def remove_line(self):
        pass

    def add_sym_load(self):
        pass

    def remove_sym_load(self):
        pass

    def set_source(self):
        pass
