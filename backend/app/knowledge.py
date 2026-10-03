import copy


def merge_facts(previous, incoming):
    """Accumulate observed facts; native views separately represent current access."""
    if isinstance(previous, dict) and isinstance(incoming, dict):
        result = copy.deepcopy(previous)
        for key, value in incoming.items():
            result[key] = merge_facts(result[key], value) if key in result else copy.deepcopy(value)
        return result
    if isinstance(previous, list) and isinstance(incoming, list):
        result = copy.deepcopy(previous)
        for value in incoming:
            if value not in result:
                result.append(copy.deepcopy(value))
        return result
    return copy.deepcopy(incoming)


class PrivateMemory:
    def __init__(self, actor):
        self.actor = actor
        self.observations = []
        self.hosts = {}
        self.reported_hosts = {}
        self.inbox = []
        self.history = []
        self.view = {}

    def observe(self, delta, native_view):
        self.view = copy.deepcopy(native_view)
        self.observations.append(copy.deepcopy(delta))
        for hostid, fields in delta["data"].items():
            if not isinstance(fields, dict):
                continue
            host = self.hosts.setdefault(hostid, {"fields": {}, "evidence_ids": [], "source": "self_observed"})
            host["fields"] = merge_facts(host["fields"], fields)
            host["evidence_ids"].append(delta["evidence_id"])
            host["last_tick"] = delta["tick"]

    def receive(self, messages):
        self.inbox.extend(copy.deepcopy(messages))

    def report(self, fragment, evidence_ids, origin, tick):
        for hostid, fields in fragment.items():
            host = self.reported_hosts.setdefault(hostid, {"fields": {}, "evidence_ids": [], "origins": [], "source": "verified_peer_report"})
            host["fields"] = merge_facts(host["fields"], fields)
            host["evidence_ids"] = list(dict.fromkeys(host["evidence_ids"] + evidence_ids))
            host["origins"] = list(dict.fromkeys(host["origins"] + [origin]))
            host["last_tick"] = tick

    def public_view(self, mission, budget):
        # This function never accepts truth or another actor's PrivateMemory.
        return {"actor": self.actor, "mission": mission, "native": copy.deepcopy(self.view), "hosts": copy.deepcopy(self.hosts), "reported_hosts": copy.deepcopy(self.reported_hosts), "inbox": copy.deepcopy(self.inbox[-24:]), "history": copy.deepcopy(self.history[-20:]), "budget": budget}

    def evidence_ids(self):
        # Address-bearing observations are retained for verified forwarding.
        return [o["evidence_id"] for o in self.observations if any(isinstance(v, dict) and ("Interface" in v or "System info" in v) for v in o["data"].values())][-16:]
