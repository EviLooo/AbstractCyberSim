"""Traffic-only route sensors and bounded temporary native service blocks.

No session/compromise inventory is accepted by the response policy. Exposure is
a declared synthetic modeling assumption, independent of native Blue Monitor.
"""
import copy
import random
from packages.contracts.route_templates import clue


class RoutePressure:
    def __init__(self, manifest, seed):
        self.manifest = manifest
        self.options = manifest.get("tradeoffs", {}).get("settings", {"enabled": False})
        self.enabled = self.options["enabled"]
        self.rules = {r["target"]: r for r in manifest.get("rules", []) if r.get("tradeoff")}
        self.rng = random.Random("route-sensors:1.0:{}".format(seed))
        self.pending = {}
        self.blocked = {}
        self.used = 0

    def assessment(self, host):
        rule = self.rules.get(host)
        return clue(rule["tradeoff"]) if rule else None

    def duration(self, host):
        rule = self.rules.get(host)
        return rule["tradeoff"]["exploit_ticks"] if rule else None

    def observe(self, traffic, tick):
        events = []
        if not self.enabled:
            return events
        for item in traffic:
            host = item["target"]
            rule = self.rules.get(host)
            if not rule:
                continue
            detected = self.rng.random() < rule["tradeoff"]["detection_probability"]
            events.append(dict(item, type="route_sensor_observation", tick=tick, detected=detected))
            if detected:
                events.append({"type": "route_sensor_alert", "host": host, "signal_tick": tick,
                               "sensor": "gateway traffic sensor", "action": item["action"]})
                if host not in self.blocked:
                    self.pending.setdefault(host, tick)
        return events

    def transition(self, tick):
        """Return declared effects using sensor alerts only, before the native tick."""
        events = []
        for host, release in sorted(list(self.blocked.items())):
            if tick >= release:
                del self.blocked[host]
                events.append({"type": "route_block_released", "host": host, "effect_tick": tick})
        if self.enabled and self.options["reactive_blocks"]:
            for seen, host in sorted((seen, host) for host, seen in self.pending.items()):
                if self.used >= self.options["response_budget"]:
                    break
                if tick < seen + self.options["reaction_delay"] or host in self.blocked:
                    continue
                del self.pending[host]
                self.used += 1
                release = tick + self.options["block_ticks"]
                self.blocked[host] = release
                events.append({"type": "route_block_started", "host": host, "signal_tick": seen,
                               "effect_tick": tick, "release_tick": release,
                               "remaining_responses": self.options["response_budget"] - self.used})
        return events

    def apply_blocks(self, state):
        """Own only entries added by this module; preserve unrelated ACL entries."""
        if not self.enabled:
            return
        if not hasattr(self, "original_block_keys"):
            self.original_block_keys = set(state.blocks)
        added_before = getattr(self, "added_blocks", set())
        for target, source in added_before:
            if target in state.blocks and source in state.blocks[target]:
                state.blocks[target].remove(source)
        for target in list(state.blocks):
            if not state.blocks[target] and target not in self.original_block_keys:
                del state.blocks[target]
        self.added_blocks = set()
        for host in sorted(self.blocked):
            for other in state.hosts:
                if host == other:
                    continue
                for target, source in ((host, other), (other, host)):
                    values = state.blocks.setdefault(target, [])
                    if source not in values:
                        values.append(source)
                        self.added_blocks.add((target, source))

    def snapshot(self):
        return {"enabled": self.enabled, "version": "1.0", "responses_used": self.used,
                "blocked_until": copy.deepcopy(self.blocked), "pending_alerts": copy.deepcopy(self.pending),
                "effect": "Service traffic blocked in both directions; existing access is not revoked"}
