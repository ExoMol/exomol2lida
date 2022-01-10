import json


class MapEncoder(json.JSONEncoder):
    """A custom encoder handling sets"""

    def default(self, obj):
        if isinstance(obj, set):
            return sorted(obj)
        return json.JSONEncoder.default(self, obj)
