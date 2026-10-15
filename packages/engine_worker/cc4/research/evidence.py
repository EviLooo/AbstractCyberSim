"""Exact allowlist for replayable evidence, never session/process transfer."""
import copy


def disclosed_fields(raw):
    result = {}
    for host, fields in raw.items():
        if not isinstance(fields, dict):
            continue
        allowed = fields.get("Research evidence")
        if allowed:
            result[host] = {"Research evidence": copy.deepcopy(allowed)}
    return result


def token_refs(fields):
    return {item["token_ref"] for host in fields.values() for item in host.get("Research evidence", [])
            if item.get("kind") == "artifact" and item.get("token_ref")}
