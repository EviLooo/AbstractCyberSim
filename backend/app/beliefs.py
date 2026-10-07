"""Recipient-local evidence history and deterministic disclosure on the world clock.

Nothing here receives truth, a defender event or another worker's memory.
"""
import copy


def scan_key(session, ip):
    return "{}:{}".format(session, ip) if session else ip


class BeliefLedger:
    def __init__(self, stale_after):
        self.stale_after = stale_after
        self.history = []
        self.latest = {}
        self.events = []

    def add(self, host, fields, eid, origin, observed_tick, received_tick, source):
        for field, value in fields.items():
            key = (host, field, source, origin)
            previous = self.latest.get(key)
            record = {"host": host, "field": field, "value": copy.deepcopy(value),
                "evidence_id": eid, "origin": origin, "source": source,
                "observed_tick": observed_tick, "received_tick": received_tick,
                "contradicts": previous["evidence_id"] if previous and previous["value"] != value else None}
            # Delayed older evidence is retained, but does not replace newer facts.
            self.history.append(record)
            if previous is None or observed_tick >= previous["observed_tick"]:
                self.latest[key] = record

    def snapshot(self, tick):
        records = []
        for record in self.latest.values():
            item = copy.deepcopy(record)
            age = max(0, tick - item["observed_tick"])
            competing = [r for r in self.latest.values() if r["host"] == item["host"] and r["field"] == item["field"] and r["value"] != item["value"]]
            item.update(age=age, stale=age >= self.stale_after,
                confirmation="self_observed" if item["source"] == "self_observed" else "unconfirmed_report",
                conflict=bool(competing))
            records.append(item)
        return {"tick": tick, "stale_after": self.stale_after, "records": records,
            "history": copy.deepcopy(self.history), "events": copy.deepcopy(self.events)}


class ObservationChannel:
    def __init__(self, delay):
        self.delay = delay
        self.pending = []

    def submit(self, delta, view, action=None):
        self.pending.append({"due_tick": delta["tick"] + (self.delay if delta["tick"] else 0),
            "observation": copy.deepcopy(delta), "view": copy.deepcopy(view), "action": copy.deepcopy(action)})

    def deliver(self, tick):
        ready = [packet for packet in self.pending if packet["due_tick"] <= tick]
        self.pending = [packet for packet in self.pending if packet["due_tick"] > tick]
        return ready


def perceived_action(record):
    """Immediate action status must not smuggle delayed ports/address evidence."""
    result = copy.deepcopy(record)
    result["state_delta"] = {k: v for k, v in result.get("state_delta", {}).items()
                             if k in ["sessions_added", "sessions_lost", "privilege_changes", "controller_changes"]}
    return result
