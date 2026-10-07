import copy
from backend.app.beliefs import BeliefLedger, ObservationChannel, scan_key
from backend.app.baselines import LocalStateTracker


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
    def __init__(self, actor, settings=None, cognition=None, track_access_loss=False):
        self.actor = actor
        self.observations = []
        self.hosts = {}
        self.reported_hosts = {}
        self.inbox = []
        self.history = []
        self.view = {}
        self.tick = 0
        self.temporal = bool(settings and settings.enabled)
        self.ledger = BeliefLedger(settings.stale_after) if self.temporal else None
        self.channel = ObservationChannel(settings.observation_delay) if self.temporal else None
        self.scan_ticks = {}
        self.scan_pending = {}
        self.epoch = 0
        self.retry_limit = cognition.action_retry_limit if cognition else 2
        self.failure_backoff = cognition.failure_backoff_ticks if cognition else 0
        self.track_access_loss = track_access_loss
        self.fact_tracker = LocalStateTracker()
        self.research_evidence = []
        self.accepted_peer_evidence = set()

    def observe(self, delta, native_view, action=None):
        self.tick = delta["tick"]
        if self.temporal:
            if action and action["proposal"]["action"] == "DiscoverNetworkServices" and action["valid"] and action["outcome"] == "TRUE":
                self.scan_pending[scan_key(action["proposal"].get("session", 0), action["proposal"]["target"])] = self.tick + self.channel.delay
            previous = self.view.get("sessions", [])
            current = native_view["sessions"]
            old = {(s["id"], s["hostname"]): s for s in previous if s["active"]}
            new = {(s["id"], s["hostname"]): s for s in current if s["active"]}
            lost = [s for identity, s in old.items() if identity not in new]
            if lost:
                self.epoch += 1
                for session in lost:
                    self.ledger.events.append({"type": "access_lost", "tick": self.tick, "host": session["hostname"], "session_id": session["id"], "source": "own_session_status"})
            lost_hosts = {e["host"] for e in self.ledger.events if e["type"] == "access_lost"}
            for identity, session in new.items():
                if identity not in old and session["hostname"] in lost_hosts:
                    self.ledger.events.append({"type": "access_recovered", "tick": self.tick, "host": session["hostname"], "session_id": session["id"], "source": "own_session_status"})
            if not self.view:
                self.view = {"actor": self.actor, "known": {k: [] for k in native_view["known"]}, "scan_cache": {}}
            self.view.update(sessions=copy.deepcopy(current), pending_action=copy.deepcopy(native_view.get("pending_action")), pivot_enabled=native_view.get("pivot_enabled", False))
            for field in ("catalog", "access_resources"):
                if field in native_view:
                    self.view[field] = copy.deepcopy(native_view[field])
            # A lost/reassigned controller cannot retain a previous session's cache.
            controllers = {str(s["id"]) for s in current if s["active"] and s["controller"]}
            self.view["scan_cache"] = {sid: cache for sid, cache in self.view["scan_cache"].items() if sid in controllers and any(s["id"] == int(sid) and (s["id"], s["hostname"]) in old for s in current)}
            self.channel.submit(delta, native_view, action)
            for packet in self.channel.deliver(self.tick):
                visible = packet["view"]
                if "possessed_tokens" in visible:
                    # Tokens acquired by inspection remain hidden until that
                    # observation is delivered. A current raw view is not proof.
                    self.view["possessed_tokens"] = sorted(set(self.view.get("possessed_tokens", [])) | set(visible["possessed_tokens"]))
                for field, values in visible["known"].items():
                    self.view["known"][field] = sorted(set(self.view["known"][field]) | set(values))
                for sid, cache in visible["scan_cache"].items():
                    recorded = next((s for s in visible["sessions"] if str(s["id"]) == sid), None)
                    if sid in controllers and recorded and (recorded["id"], recorded["hostname"]) in new:
                        self.view["scan_cache"][sid] = copy.deepcopy(cache)
                received = dict(packet["observation"], received_tick=self.tick)
                self._remember(received)
                completed = packet["action"]
                if completed and completed["proposal"]["action"] == "DiscoverNetworkServices" and completed["valid"] and completed["outcome"] == "TRUE":
                    self.scan_ticks[scan_key(completed["proposal"].get("session", 0), completed["proposal"]["target"])] = received["tick"]
            return
        if native_view.get("pivot_enabled") or self.track_access_loss:
            old = {(s["id"], s["hostname"]) for s in self.view.get("sessions", []) if s["active"]}
            new = {(s["id"], s["hostname"]) for s in native_view["sessions"] if s["active"]}
            if old - new:
                self.epoch += 1
        self.view = copy.deepcopy(native_view)
        self._remember(delta)

    def _remember(self, delta):
        self.observations.append(copy.deepcopy(delta))
        for hostid, fields in delta["data"].items():
            if not isinstance(fields, dict):
                continue
            host = self.hosts.setdefault(hostid, {"fields": {}, "evidence_ids": [], "source": "self_observed"})
            host["fields"] = {**host["fields"], **copy.deepcopy(fields)} if self.temporal else merge_facts(host["fields"], fields)
            host["evidence_ids"].append(delta["evidence_id"])
            host["last_tick"] = delta["tick"]
            self._research_records(hostid, fields, delta["evidence_id"], self.actor,
                                   delta["tick"], delta.get("received_tick", delta["tick"]), "self_observed")
            if self.temporal:
                host["received_tick"] = delta["received_tick"]
                self.ledger.add(hostid, fields, delta["evidence_id"], self.actor, delta["tick"], delta["received_tick"], "self_observed")

    def receive(self, messages):
        self.inbox.extend(copy.deepcopy(messages))

    def _research_records(self, host, fields, eid, origin, observed_tick, received_tick, source):
        for item in fields.get("Research evidence", []):
            record = {"host": host, "evidence_id": eid, "origin": origin,
                      "observed_tick": observed_tick, "received_tick": received_tick,
                      "source": source, **copy.deepcopy(item)}
            # Repeated delivery cannot refresh the original observation or
            # multiply a record simply because it arrived on another tick.
            if not any(r["evidence_id"] == eid and r["host"] == host and
                       all(r.get(k) == v for k, v in item.items()) for r in self.research_evidence):
                self.research_evidence.append(record)

    def report(self, fragment, evidence_ids, origin, tick, evidence=None):
        for hostid, fields in fragment.items():
            host = self.reported_hosts.setdefault(hostid, {"fields": {}, "evidence_ids": [], "origins": [], "source": "verified_peer_report"})
            host["fields"] = merge_facts(host["fields"], fields)
            host["evidence_ids"] = list(dict.fromkeys(host["evidence_ids"] + evidence_ids))
            host["origins"] = list(dict.fromkeys(host["origins"] + [origin]))
            host["last_tick"] = tick
        if self.temporal:
            for item in evidence or []:
                for hostid, fields in item["data"].items():
                    self._research_records(hostid, fields, item["evidence_id"], origin, item["tick"], tick, "verified_peer_report")
                    self.ledger.add(hostid, fields, item["evidence_id"], origin, item["tick"], tick, "verified_peer_report")
                    self.reported_hosts[hostid]["last_tick"] = max(r["observed_tick"] for r in self.ledger.latest.values() if r["host"] == hostid and r["source"] == "verified_peer_report")
                    self.reported_hosts[hostid]["received_tick"] = tick
            for hostid in fragment:
                current = [r for r in self.ledger.latest.values() if r["host"] == hostid and r["source"] == "verified_peer_report"]
                fields = {}
                for record in sorted(current, key=lambda r: (r["observed_tick"], r["received_tick"])):
                    fields[record["field"]] = copy.deepcopy(record["value"])
                if fields:
                    self.reported_hosts[hostid]["fields"] = fields

    def accept_intel_view(self, update):
        if not self.temporal:
            self.view = update["view"]
            return
        # Only the validated delivered address fragment changes knowledge;
        # raw native views may already contain locally queued discoveries.
        if "possessed_tokens" in update["view"]:
            refs = {r["token_ref"] for fields in update["address_fragment"].values()
                    for r in fields.get("Research evidence", []) if r.get("token_ref")}
            self.view["possessed_tokens"] = sorted(set(self.view.get("possessed_tokens", [])) | refs)
        for hostid, fields in update["address_fragment"].items():
            if "." in hostid and hostid not in self.view["known"]["ip_address"]:
                self.view["known"]["ip_address"].append(hostid)
            hostname = fields.get("System info", {}).get("Hostname")
            if hostname and hostname not in self.view["known"]["hostname"]:
                self.view["known"]["hostname"].append(hostname)
            for interface in fields.get("Interface", []):
                for field, key in [("ip_address", "IP Address"), ("subnet", "Subnet")]:
                    value = interface.get(key)
                    if value is not None and str(value) not in self.view["known"][field]:
                        self.view["known"][field].append(str(value))

    def advance_clock(self, tick):
        self.tick = tick

    def public_view(self, mission, budget):
        # This function never accepts truth or another actor's PrivateMemory.
        result = {"actor": self.actor, "mission": mission, "native": copy.deepcopy(self.view), "hosts": copy.deepcopy(self.hosts), "reported_hosts": copy.deepcopy(self.reported_hosts), "inbox": copy.deepcopy(self.inbox[-24:]), "history": copy.deepcopy(self.history[-20:]), "budget": budget, "belief_epoch": self.epoch}
        if self.temporal:
            result["beliefs"] = self.ledger.snapshot(self.tick)
            result["beliefs"].update(epoch=self.epoch, scan_ticks=copy.deepcopy(self.scan_ticks))
        if "catalog" in self.view:
            from backend.app.research_agents import candidates
            result["eligible_candidates"] = candidates(self)
            result["coordination"] = copy.deepcopy(getattr(self, "coordination", {}))
            result["research_evidence"] = [dict(copy.deepcopy(r), age=max(0, self.tick - r["observed_tick"]),
                stale=self.temporal and self.tick - r["observed_tick"] >= self.ledger.stale_after)
                for r in self.research_evidence]
        self.fact_tracker.update(result, self.tick)
        result["local_state"] = self.fact_tracker.snapshot()
        return result

    def evidence_ids(self):
        # Address-bearing observations are retained for verified forwarding.
        return [o["evidence_id"] for o in self.observations if any(isinstance(v, dict) and ("Interface" in v or "System info" in v or "Route clue" in v or "Research evidence" in v) for v in o["data"].values())][-16:]
