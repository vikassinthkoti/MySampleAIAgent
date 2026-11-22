import json

def from_json(data, *args, **kwargs):
    if isinstance(data, (bytes, bytearray)):
        data = data.decode("utf-8")
    return json.loads(data)

def cache_clear(*args, **kwargs):
    pass

__version__ = "0.8.2"