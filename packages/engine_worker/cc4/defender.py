"""Bounded response to a defender's native Monitor observations only.

No true compromise inventory is accepted by this policy. Traffic/process signals
may produce unnecessary restores; this is an explicit simple research control.
"""


class RestorePolicy:
    def __init__(self, settings):
        self.delay = settings["response_delay"]
        self.cooldown = settings["response_cooldown"]
        self.budget = settings["response_budget"]
        self.pending = {}
        self.last_response = {}
        self.used = 0

    def observe(self, observation, tick):
        signals = []
        for host, data in observation.items():
            if not isinstance(data, dict) or not data.get("Processes"):
                continue
            # Monitor indexes events by the sensor's host. The combined native
            # observation may carry unrelated System info from prior actions.
            name = host
            if tick - self.last_response.get(name, -self.cooldown) < self.cooldown:
                continue
            if name not in self.pending:
                self.pending[name] = tick
                signals.append({"type": "defender_signal", "host": name, "signal_tick": tick})
        return signals

    def choose(self, tick, allowed_hosts):
        if self.used >= self.budget:
            return None
        choices = sorted((seen, host) for host, seen in self.pending.items()
                         if tick - seen >= self.delay and host in allowed_hosts)
        if not choices:
            return None
        seen, host = choices[0]
        del self.pending[host]
        self.last_response[host] = tick
        self.used += 1
        return {"host": host, "signal_tick": seen, "decision_tick": tick,
                "remaining_responses": self.budget - self.used}
