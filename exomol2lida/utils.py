import json

EV_IN_CM = 8_065.73


class MapEncoder(json.JSONEncoder):
    """A custom encoder handling sets"""

    def default(self, obj):
        if isinstance(obj, set):
            return sorted(obj)
        return json.JSONEncoder.default(self, obj)
