"""Versioned local-information policies. No engine, world or truth imports.

The tracker remembers only facts present in a worker input. The replanner ranks
observed action frontiers using optimistic action-cost estimates, not a hidden
network map or a claim of an optimal real-world path.
"""
import copy
from ipaddress import ip_address

VERSION = "1.2"
ACTION_COSTS = {"DiscoverRemoteSystems": 1, "DiscoverNetworkServices": 1,
                "ExploitRemoteService": 4, "PrivilegeEscalate": 2, "EstablishPivot": 2}
RULE_ORDER = {"PrivilegeEscalate": 0, "EstablishPivot": 1,
              "ExploitRemoteService": 2, "DiscoverNetworkServices": 3,
              "DiscoverRemoteSystems": 4}


def action_key(p):
    return (p["action"], p.get("target"), p.get("session", 0))


def describe_policy(name):
    from backend.app.research_policy import NAMES, describe
    if name in NAMES:
        return describe(name)
    if name == "local_search":
        return {"id": name, "version": "1.0", "information": "own observations and delivered reports only",
                "search": "bounded uniform-cost search with time/score Pareto labels; next observed goal or information frontier",
                "qualification": "optimistic abstract transitions and ordinal risk penalties; no calibrated success probabilities or joint-mission optimality"}
    return {"id": name, "version": VERSION, "information": "own observations and delivered reports only",
            "search": "observed action frontiers; optimistic action costs" if name == "local_replan" else "fixed technical-stage priorities",
            "cost_estimates": ACTION_COSTS if name == "local_replan" else {},
            "qualification": "software fixtures only; no measured model advantage"}


class LocalStateTracker:
    """Deterministic remembered observations, independently testable from strategy."""
    def __init__(self):
        self.controllers = {}
        self.address_names = {}
        self.address_first_seen = {}
        self.failures = {}
        self.completed = set()
        self.last_signature = None
        self.epoch = 0
        self.service_edges = {}

    def snapshot(self):
        return {"version": VERSION, "controllers": copy.deepcopy(self.controllers),
                "address_names": copy.deepcopy(self.address_names),
                "address_first_seen": copy.deepcopy(self.address_first_seen),
                "observed_service_edges": [dict(source_host=source, target_address=target, **copy.deepcopy(record))
                                           for (source, target), record in sorted(self.service_edges.items())],
                "observed_failures": [{"action": k[0], "target": k[1], "session": k[2], "count": n}
                                      for k, n in self.failures.items()], "belief_epoch": self.epoch}

    def update(self, view, tick):
        native = view["native"]
        known_addresses = native.get("known", {}).get("ip_address", [])
        controllers = {s["id"]: s["hostname"] for s in native.get("sessions", []) if s["active"] and s["controller"]}
        previous = self.controllers
        lost = sorted(sid for sid, host in previous.items() if controllers.get(sid) != host)
        added = sorted(sid for sid, host in controllers.items() if previous.get(sid) != host)
        epoch = view.get("belief_epoch", view.get("beliefs", {}).get("epoch", 0))
        if epoch != self.epoch or lost:
            self.failures.clear()
            self.completed.clear()
        self.epoch = epoch
        self.controllers = controllers
        for sid, cache in native.get("scan_cache", {}).items():
            source = controllers.get(int(sid))
            if source:
                for target, ports in cache.items():
                    if ports:
                        self.service_edges.setdefault((source, target), {"ports": copy.deepcopy(ports),
                            "first_seen_tick": tick, "last_positive_tick": tick, "belief_epoch": epoch,
                            "source": "own positive native service cache; historical belief, not current ACL truth"})
        for ip in known_addresses:
            self.address_first_seen.setdefault(ip, tick)
        for host_id, host in view.get("hosts", {}).items():
            fields = host.get("fields", {})
            name = fields.get("System info", {}).get("Hostname")
            if not name:
                try:
                    ip_address(host_id)
                except ValueError:
                    # Native inventory can identify a host by its observation
                    # key without repeating a System info/Hostname field.
                    name = host_id
            if name:
                for iface in fields.get("Interface", []):
                    ip = str(iface.get("IP Address", ""))
                    if ip in known_addresses:
                        self.address_names[ip] = name
        for action in view.get("history", []):
            if action.get("belief_epoch", 0) != epoch or action["proposal"]["action"] == "Sleep":
                continue
            if action.get("outcome") == "IN_PROGRESS":
                continue
            identity = (action.get("started_tick", 0), action_key(action["proposal"]))
            if identity in self.completed:
                continue
            self.completed.add(identity)
            proposal = action["proposal"]
            if proposal["action"] == "DiscoverNetworkServices" and action.get("outcome") == "TRUE" and action.get("valid", True):
                source = controllers.get(proposal.get("session", 0))
                edge = self.service_edges.get((source, proposal.get("target")))
                if edge:
                    edge.update(last_positive_tick=action.get("observed_tick", action.get("completed_tick", tick)), belief_epoch=epoch)
            if action.get("outcome") == "FALSE" or not action.get("valid", True):
                k = action_key(action["proposal"])
                self.failures[k] = self.failures.get(k, 0) + 1
        signature = (tuple(sorted(controllers.items())), tuple(sorted(known_addresses)),
                     repr(native.get("scan_cache", {})), epoch)
        changed = signature != self.last_signature
        self.last_signature = signature
        return {"changed": changed, "lost_controllers": lost, "new_controllers": added,
                "belief_epoch": epoch, "known_addresses": len(known_addresses)}


class BaselinePolicy:
    def __init__(self, name):
        self.name = name
        self.tracker = LocalStateTracker()

    def rank(self, view, candidates, tick):
        changes = self.tracker.update(view, tick)
        native = view["native"]
        mission = view.get("mission", {})
        goals = set(mission.get("target_names", []))
        requirements = mission.get("requirements") or {}
        for objective in requirements.get("objectives", []):
            goals.update(objective.get("requires_privileged_hosts", []))
        privileged = {s["hostname"] for s in native["sessions"] if s["active"] and s["privileged"]}
        missing = goals - privileged
        holding = bool(goals) and not missing
        controllers = list(self.tracker.controllers)
        scored = []
        for p in candidates:
            label, target, sid = action_key(p)
            host = self.tracker.address_names.get(target, target)
            goal = host in missing
            refresh = label == "DiscoverNetworkServices" and p.get("rationale", "").startswith("Refresh aged service evidence")
            failures = self.tracker.failures.get(action_key(p), 0)
            transport_failures = self.tracker.failures.get(('DiscoverNetworkServices', target, sid), 0)
            scanned_ports = native.get('scan_cache', {}).get(str(sid), {}).get(target, [])
            source_age = len(controllers) - 1 - controllers.index(sid) if sid in controllers else len(controllers)
            cost = ACTION_COSTS.get(label, 0)
            observed_clue = None
            # Observed/delivered assessments are beliefs, never a hidden route
            # map. All providers receive the same evidence through memory.
            for collection in (view.get("reported_hosts", {}), view.get("hosts", {})):
                assessment = collection.get(str(target), {}).get("fields", {}).get("Route clue")
                if assessment:
                    observed_clue = assessment
            if label == "ExploitRemoteService" and observed_clue:
                cost = observed_clue.get("estimated_exploit_ticks", cost)
            # Remaining steps are optimistic: services/accounts can still fail.
            remaining = {"DiscoverNetworkServices": 6, "ExploitRemoteService": 2,
                         "PrivilegeEscalate": 0, "EstablishPivot": 1,
                         "DiscoverRemoteSystems": 7}.get(label, 0)
            if self.name == "local_rules":
                rank = (1 if refresh else RULE_ORDER.get(label, 9), source_age, 0 if goal else 1, failures, str(target))
                reason = "Fixed technical-stage priority, then newest owned source and observed mission host"
            else:
                # Finish owned footholds first. Then consider observed goals,
                # fresh scans, failure cost, and new-source exploration frontiers.
                phase = 0 if label in ("PrivilegeEscalate", "EstablishPivot") else 1 if goal else 2
                rank = (phase, transport_failures + failures, 0 if scanned_ports else 1, source_age, 0 if refresh else 1, cost + remaining,
                        -self.tracker.address_first_seen.get(target, 0), str(target))
                reason = "Replan from observed goals, source ownership, scan age, failures and estimated remaining action cost"
            scored.append({"proposal": copy.deepcopy(p), "rank": list(rank), "observed_goal": goal,
                "observed_failures": failures, "estimated_action_ticks": cost,
                "observed_service_evidence": bool(scanned_ports), "observed_transport_failures": transport_failures,
                "estimated_remaining_ticks": remaining, "reason": reason})
            scored[-1]["observed_route_clue"] = copy.deepcopy(observed_clue)
        scored.sort(key=lambda row: tuple(row["rank"]))
        if holding:
            scored = []
        trace = {"policy": self.name, "version": VERSION, "tick": tick, "actor": view["actor"],
                 "state_change": changes, "own_missing_goals": sorted(missing),
                 "status": "holding_own_goals" if holding else "considering_frontiers" if scored else "no_eligible_action",
                 "candidate_count": len(scored), "alternatives": scored[:12],
                 "omitted_alternatives": max(0, len(scored) - 12)}
        return [row["proposal"] for row in scored], trace
