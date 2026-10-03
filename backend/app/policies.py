"""Organizations route tasks/claims. Cognition sees private/delivered data only."""
import hashlib
from packages.contracts.models import ActionProposal


def key(proposal):
    return f"{proposal['action']}:{proposal.get('target') or ''}"


def candidates(memory):
    view = memory.view
    controllers = [s for s in view.get("sessions", []) if s["active"] and s["controller"]]
    if not controllers:
        return []
    controller = controllers[0]["id"]
    cache = view["scan_cache"].get(str(controller), {})
    history = memory.history
    attempts = {}
    successes = set()
    for action in history:
        k = key(action["proposal"])
        attempts[k] = attempts.get(k, 0) + 1
        if action.get("valid") and action.get("outcome") == "TRUE":
            successes.add(k)
    own_names = {s["hostname"] for s in view.get("sessions", []) if s["active"]}
    own_addresses = set()
    for hostid, host in memory.hosts.items():
        if host["fields"].get("System info", {}).get("Hostname") in own_names:
            for iface in host["fields"].get("Interface", []):
                ip = iface.get("IP Address")
                if ip:
                    own_addresses.add(str(ip))
            if "." in hostid:
                own_addresses.add(hostid)
    proposed = []

    def add(action, target, reason):
        p = ActionProposal(action=action, session=controller, target=target, rationale=reason).model_dump()
        k = key(p)
        if k not in successes and attempts.get(k, 0) < 2:
            proposed.append(p)

    for s in view["sessions"]:
        if s["active"] and not s["privileged"] and s["hostname"] in view["known"]["hostname"]:
            add("PrivilegeEscalate", s["hostname"], "Escalate an actor-owned foothold and inspect its locally accessible information")
    for ip, ports in sorted(cache.items()):
        if ports and ip not in own_addresses:
            add("ExploitRemoteService", ip, "Use this actor's own observed service scan; CybORG selects the concrete exploit")
    for ip in sorted(view["known"]["ip_address"]):
        if ip not in cache and ip not in own_addresses and ip != "127.0.0.1":
            add("DiscoverNetworkServices", ip, "Scan services at an observed address")
    for subnet in sorted(view["known"]["subnet"]):
        add("DiscoverRemoteSystems", subnet, "Discover reachable hosts in an observed subnet")
    return proposed


class Organization:
    def __init__(self, config, actors):
        self.config = config
        self.actors = actors
        self.reports = {}
        self.coordinator_inbox = []
        self.assignments = {}
        self.finished = set()

    def coordinator_view(self, deliveries, tick):
        self.coordinator_inbox.extend(deliveries)
        for m in deliveries:
            if m["kind"] == "report":
                self.reports[m["sender"]] = m
                for h in m["payload"].get("recent_actions", []):
                    if h.get("outcome") == "TRUE" and h.get("valid"):
                        self.finished.add(key(h["proposal"]))
        return {"role": "coordinator", "tick": tick, "workers": self.actors, "delivered_reports": list(self.reports.values()), "completed_action_keys": sorted(self.finished)}

    def scripted_assignments(self):
        chosen = set()
        result = {}
        pool = []
        for report in self.reports.values():
            for p in report["payload"].get("candidates", []):
                if key(p) not in self.finished:
                    pool.append((p, report))
        priority = {"PrivilegeEscalate": 0, "ExploitRemoteService": 1, "DiscoverNetworkServices": 2, "DiscoverRemoteSystems": 3}
        pool.sort(key=lambda pair: (priority.get(pair[0]["action"], 9), key(pair[0])))
        for actor in self.actors:
            for p, report in pool:
                k = key(p)
                if k in chosen:
                    continue
                # Sessions/privileges/caches cannot be delegated. Only discovery
                # and rescanning a delivered address can move between workers.
                if p["action"] in ["PrivilegeEscalate", "ExploitRemoteService"] and report["sender"] != actor:
                    continue
                chosen.add(k)
                result[actor] = {"proposal": dict(p, session=0), "evidence_ids": report["evidence_ids"], "origin": report["sender"]}
                break
        return result

    def preferred(self, memory, tick):
        options = candidates(memory)
        architecture = self.config.team.architecture
        if architecture == "hierarchy":
            tasks = [m for m in memory.inbox if m["kind"] == "assignment" and tick - m["created_tick"] <= self.config.team.claim_ttl]
            if not tasks:
                return ActionProposal(action="Sleep", rationale="Waiting for a delivered coordinator assignment").model_dump()
            task = tasks[-1]["payload"]["proposal"]
            self.assignments[memory.actor] = task
            matching = next((p for p in options if key(p) == key(task)), None)
            return matching or ActionProposal(action="Sleep", rationale="Assignment is complete or its local prerequisites are unavailable").model_dump()
        if architecture == "swarm":
            claims = {}
            for m in memory.inbox:
                if m["kind"] == "claim" and tick - m["created_tick"] <= self.config.team.claim_ttl:
                    claims.setdefault(m["payload"]["action_key"], set()).add(m["sender"])
            available = []
            for p in options:
                claimants = claims.get(key(p), set()) | {memory.actor}
                # Local deterministic tie breaking from delivered claims only.
                if min(claimants) == memory.actor:
                    available.append(p)
            def rank(p):
                # Keep technical stage priority while varying local target
                # preference; there is no shared allocator or private blackboard.
                stage = {"PrivilegeEscalate": 0, "ExploitRemoteService": 1, "DiscoverNetworkServices": 2, "DiscoverRemoteSystems": 3}[p["action"]]
                digest = hashlib.sha256(f"{memory.actor}:{key(p)}".encode()).hexdigest()
                return stage, digest
            available.sort(key=rank)
            options = available
        return options[0] if options else ActionProposal(action="Sleep", rationale="No locally eligible uncompleted action").model_dump()
