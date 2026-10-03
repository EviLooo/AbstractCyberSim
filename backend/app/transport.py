"""Experimental communication overlay; not native simulated network traffic."""
import copy
import json
import random


class MessageBus:
    def __init__(self, config, actors, architecture):
        self.config = config
        self.actors = list(actors)
        self.architecture = architecture
        self.reasoners = self.actors + (["Coordinator"] if architecture == "hierarchy" else [])
        self.rng = random.Random(config.seed)
        self.messages = []
        self.counter = 0

    def neighbors(self, sender):
        if self.architecture == "independent":
            return []
        if self.architecture == "hierarchy":
            return self.actors if sender == "Coordinator" else ["Coordinator"]
        return [a for a in self.actors if a != sender]

    def enqueue(self, sender, recipients, kind, payload, evidence, tick):
        if sender not in self.reasoners or any(r not in self.neighbors(sender) for r in recipients):
            raise ValueError("Message violates the organization's communication topology")
        emitted = []
        for recipient in sorted(set(recipients)):
            self.counter += 1
            message = {"id": f"m{self.counter}", "sender": sender, "recipient": recipient, "kind": kind, "payload": copy.deepcopy(payload), "evidence_ids": list(evidence), "created_tick": tick, "due_tick": tick + 1 + self.config.extra_delay, "expires_tick": tick + self.config.ttl, "status": "pending"}
            message["bytes"] = len(json.dumps(message, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8"))
            self.messages.append(message)
            emitted.append(message)
        return emitted

    def deliver(self, tick):
        deliveries = {a: [] for a in self.reasoners}
        used_bytes = used_envelopes = 0
        changes = []
        for message in self.messages:
            if message["status"] != "pending":
                continue
            if tick > message["expires_tick"]:
                message.update(status="expired", resolved_tick=tick)
            elif tick < message["due_tick"]:
                continue
            elif self.rng.random() < self.config.loss_probability:
                message.update(status="dropped_loss", resolved_tick=tick)
            elif used_envelopes >= self.config.envelopes_per_tick or used_bytes + message["bytes"] > self.config.bytes_per_tick:
                message.update(status="dropped_capacity", resolved_tick=tick)
            else:
                message.update(status="delivered", resolved_tick=tick)
                used_bytes += message["bytes"]
                used_envelopes += 1
                deliveries[message["recipient"]].append(copy.deepcopy(message))
            changes.append(copy.deepcopy(message))
        return deliveries, changes

    def snapshot(self):
        return copy.deepcopy(self.messages)
