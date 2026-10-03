import copy


class PrivateMemory:
    def __init__(self, actor):
        self.actor = actor
        self.observations = []
        self.hosts = {}
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
            host["fields"].update(copy.deepcopy(fields))
            host["evidence_ids"].append(delta["evidence_id"])
            host["last_tick"] = delta["tick"]

    def receive(self, messages):
        self.inbox.extend(copy.deepcopy(messages))

    def public_view(self, mission, budget):
        # This function never accepts truth or another actor's PrivateMemory.
        return {"actor": self.actor, "mission": mission, "native": copy.deepcopy(self.view), "hosts": copy.deepcopy(self.hosts), "inbox": copy.deepcopy(self.inbox[-24:]), "history": copy.deepcopy(self.history[-20:]), "budget": budget}

    def evidence_ids(self):
        # Address-bearing observations are retained for verified forwarding.
        return [o["evidence_id"] for o in self.observations if any(isinstance(v, dict) and ("Interface" in v or "System info" in v) for v in o["data"].values())][-16:]
