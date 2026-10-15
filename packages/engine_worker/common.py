"""Engine-neutral serialization shared by the isolated adapters."""
import json


def normalized(value):
    if isinstance(value, dict):
        return {str(k): normalized(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [normalized(x) for x in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if hasattr(value, "name"):
        return value.name
    if hasattr(value, "tolist"):
        return normalized(value.tolist())
    return str(value)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
