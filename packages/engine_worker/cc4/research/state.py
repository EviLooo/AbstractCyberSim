"""Engine-private capabilities; actor possession is explicit and auditable."""
import copy


class ResearchState:
    def __init__(self, manifest, actors):
        self.manifest = copy.deepcopy(manifest)
        self.tokens = self.manifest["tokens"]
        self.artifacts = self.manifest["artifacts"]
        self.possession = {actor: set() for actor in actors}
        self.attempts = []
        self.attempt_limit = manifest["attempt_limit"]
        self.response = {"budget": manifest["change"]["response_budget"], "pending": None, "events": []}

    def reserve(self, actor, proposal, tick):
        if len(self.attempts) >= self.attempt_limit:
            raise ValueError("Shared access-attempt budget exhausted")
        record = {"id": "attempt-{}".format(len(self.attempts) + 1), "actor": actor,
                  "proposal": copy.deepcopy(proposal), "admitted_tick": tick, "status": "pending"}
        self.attempts.append(record)
        return record["id"]

    def permits(self, actor, token, hostname):
        definition = self.tokens.get(token)
        return bool(token in self.possession.get(actor, ()) and definition and definition["valid"] and definition["host"] == hostname)

    def local_artifacts(self, actor, hostname, privileged):
        result = []
        for artifact in self.artifacts.get(hostname, []):
            if artifact["read"] == "root" and not privileged:
                continue
            result.append(copy.deepcopy(artifact["public"]))
            token = artifact["public"].get("token_ref")
            if token:
                self.possession[actor].add(token)
        return result

    def public_resources(self):
        return {"limit": self.attempt_limit, "reserved": len(self.attempts),
                "remaining": self.attempt_limit - len(self.attempts),
                "settled": sum(a["status"] != "pending" for a in self.attempts)}
