"""One shared response to observed traffic, never a compromise-state oracle."""
import copy

from CybORG.Shared import Observation
from CybORG.Simulator.Actions.Action import Action
from CybORG.Simulator.Actions import Restore


class PatchService(Action):
    def __init__(self, session, agent, hostname):
        super().__init__()
        self.session, self.agent, self.hostname = session, agent, hostname
        self.priority = 0

    def execute(self, state):
        if self.session not in state.sessions.get(self.agent, {}):
            return Observation(False)
        if not any(s.active and s.hostname == self.hostname for s in state.sessions[self.agent].values()):
            return Observation(False)
        host = state.hosts[self.hostname]
        # Update active and backup service conditions; preserve listening ports
        # and all owned sessions. No actor's scan cache or evidence is touched.
        for processes in (host.processes, getattr(host, "default_processes", []),
                          getattr(host, "original_processes", [])):
            for process in processes:
                if any(c.local_port == 80 for c in process.connections):
                    process.properties = [p for p in process.properties if p != "rfi"]
        return Observation(True)

    def __str__(self):
        return "PatchService {}".format(self.hostname)


class SharedResponse:
    def __init__(self, options, protected_hosts):
        self.options = copy.deepcopy(options)
        self.protected = set(protected_hosts)
        self.used = 0
        self.pending = {}
        self.inflight = None
        self.history = []

    def observe(self, traffic, tick, coverage):
        events = []
        if self.options["mode"] == "none":
            return events
        for signal in traffic:
            host = signal["target"]
            if host not in self.protected or host not in coverage or host in self.pending:
                continue
            event = {"type": "research_defender_signal", "host": host, "signal_tick": tick,
                     "sensor": "qualified reachable service traffic", "action": signal["action"]}
            self.pending[host] = tick
            events.append(event)
        self.history.extend(copy.deepcopy(events))
        return events

    def choose(self, tick, controller):
        if self.used >= self.options["response_budget"] or self.inflight:
            return None
        for seen, host in sorted((seen, host) for host, seen in self.pending.items()):
            if tick < seen + self.options["response_delay"]:
                continue
            for name in sorted(controller.agent_interfaces):
                if not name.startswith("blue_") or controller.actions_in_progress.get(name):
                    continue
                if not any(s.active and s.hostname == host for s in controller.state.sessions[name].values()):
                    continue
                kind = PatchService if self.options["mode"] == "patch_rfi" else Restore
                native = kind(session=0, agent=name, hostname=host)
                checked = controller.replace_action_if_invalid(native, controller.agent_interfaces[name])
                if type(checked).__name__ == "InvalidAction":
                    continue
                self.used += 1
                del self.pending[host]
                event = {"type": "research_defender_decision", "host": host, "actor": name,
                         "signal_tick": seen, "decision_tick": tick, "action": kind.__name__,
                         "duration": native.duration, "remaining_responses": self.options["response_budget"] - self.used}
                self.inflight = event
                self.history.append(copy.deepcopy(event))
                return name, native, event
        return None

    def complete(self, trace, tick):
        events = []
        if self.inflight:
            event = self.inflight
            executed = next((r for r in trace if r["actor"] == event["actor"] and
                             r["phase"] == "joint" and r["action"] == "{} {}".format(event["action"], event["host"])), None)
            if executed:
                events = [{"type": "research_defender_effect", "host": event["host"],
                           "actor": event["actor"], "action": event["action"],
                           "effect_tick": tick, "outcome": executed["outcome"]}]
                self.history.extend(copy.deepcopy(events))
                self.inflight = None
        return events

    def snapshot(self):
        return {"budget": self.options["response_budget"], "used": self.used,
                "pending": copy.deepcopy(self.pending), "inflight": copy.deepcopy(self.inflight),
                "history": copy.deepcopy(self.history)}
