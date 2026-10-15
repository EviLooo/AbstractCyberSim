"""Organizations route tasks/claims. Cognition sees private/delivered data only."""
import hashlib
import copy
from packages.contracts.models import ActionProposal
from backend.app.beliefs import scan_key
from backend.app.baselines import BaselinePolicy
from backend.app.search_policy import SearchPolicy
from backend.app.research_policy import ResearchPolicy, NAMES

ORGANIZATION_VERSION = "1.1"


def key(proposal):
    base = f"{proposal['action']}:{proposal.get('target') or ''}"
    result = base + (f":session={proposal['session']}" if proposal.get('session', 0) else "")
    for field in ("source_host", "method", "probe", "port", "token_ref"):
        if proposal.get(field) is not None:
            result += f":{field}={proposal[field]}"
    if proposal.get("basis_evidence_ids"):
        result += ":evidence=" + ",".join(sorted(proposal["basis_evidence_ids"]))
    return result


def stage(proposal):
    if proposal["action"] == "DiscoverNetworkServices" and proposal.get("rationale", "").startswith("Refresh aged service evidence"):
        return 1
    return {"PrivilegeEscalate": 0, "EstablishPivot": 1, "ExploitRemoteService": 2, "DiscoverNetworkServices": 3, "DiscoverRemoteSystems": 4}.get(proposal["action"], 9)


def candidates(memory):
    if memory.view.get("catalog"):
        from backend.app.research_agents import candidates as research_candidates
        return research_candidates(memory)
    controllers = [s for s in memory.view.get("sessions", []) if s["active"] and s["controller"]]
    if memory.view.get("pending_action"):
        return []
    # Every controller uses its own cache and action history. Prefer newer local
    # footholds, but never consult the route manifest or hidden firewall truth.
    return sorted([p for s in reversed(controllers) for p in _from_controller(memory, s["id"])], key=stage)


def _from_controller(memory, controller):
    view = memory.view
    if view.get("pending_action"):
        return []
    cache = view["scan_cache"].get(str(controller), {})
    history = memory.history
    attempts = {}
    failures = {}
    successes = set()
    for action in history:
        if (memory.temporal or view.get("pivot_enabled") or memory.track_access_loss) and action.get("belief_epoch", 0) != memory.epoch:
            continue
        k = key(action["proposal"])
        if action.get("submitted", True):
            attempts[k] = attempts.get(k, 0) + 1
        if action.get("valid") and action.get("outcome") == "TRUE":
            successes.add(k)
        if action.get("outcome") == "FALSE" or not action.get("valid", True):
            failures[k] = action.get("observed_tick", action.get("completed_tick", action.get("started_tick", 0)))
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

    def add(action, target, reason, refresh=False):
        p = ActionProposal(action=action, session=controller, target=target, rationale=reason).model_dump()
        k = key(p)
        cooled = memory.tick - failures.get(k, -10000) >= memory.failure_backoff
        allowed = cooled and (refresh or (k not in successes and attempts.get(k, 0) < memory.retry_limit))
        if allowed and not any(key(existing) == k for existing in proposed):
            proposed.append(p)

    for s in view["sessions"]:
        if s["active"] and (not s["privileged"] or not s["controller"]) and s["hostname"] in view["known"]["hostname"]:
            # Native PrivilegeEscalate also runs ExploreHost. A remote exploit
            # can already grant SYSTEM/root without revealing the host's intel.
            add("PrivilegeEscalate", s["hostname"], "Escalate or inspect an actor-owned foothold, including information on an already privileged host")
        if view.get("pivot_enabled") and s["active"] and s["privileged"] and not s["controller"]:
            add("EstablishPivot", s["hostname"], "Deploy a local pivot on this actor's privileged shell; its service cache starts empty")
    for ip, ports in sorted(cache.items()):
        if ip not in own_addresses:
            evidence_key = scan_key(controller, ip)
            stale = memory.temporal and memory.tick - memory.scan_ticks.get(evidence_key, 0) >= memory.ledger.stale_after
            if stale:
                refresh_attempts = sum(r.get("submitted", True) and r["proposal"]["action"] == "DiscoverNetworkServices" and r["proposal"].get("session", 0) == controller and r["proposal"].get("target") == ip and r.get("started_tick", 0) > memory.scan_ticks.get(evidence_key, 0) and r.get("belief_epoch", 0) == memory.epoch for r in history)
                if memory.scan_pending.get(evidence_key, -1) <= memory.tick and refresh_attempts < memory.retry_limit:
                    add("DiscoverNetworkServices", ip, "Refresh aged service evidence before attempting this route", refresh=True)
                if ports:
                    # Age changes the scripted recommendation, not the legal
                    # catalog. Both organizations may choose to risk old scans.
                    add("ExploitRemoteService", ip, "Own service evidence is aged; verification is recommended, but native eligibility still applies")
            elif ports:
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
        name = config.cognition.scripted_policy
        self.baselines = {a: ResearchPolicy(name, config.cognition.action_retry_limit, config.cognition.failure_backoff_ticks) if name in NAMES
                          else SearchPolicy(config.cognition.search.model_dump()) if name == "local_search"
                          else BaselinePolicy(name) for a in actors}
        self.decisions = {}
        self.claim_intents = {}
        self.claim_started = {}
        self.access_assignments = {}

    def admit_hierarchy_assignments(self, tasks, tick):
        """Leader reservations use issued tasks and delivered reports only.

        A report round trip can outlast a joint tick. Deduplication within one
        assignment batch alone cannot prevent a later duplicate admission.
        """
        for actor, reservation in list(self.access_assignments.items()):
            report = self.reports.get(actor)
            finished = bool(report and any(
                h.get('observed_tick',-1)>=reservation['issued_tick']
                and h.get('remaining_ticks',0)==0 and h.get('outcome') in ('TRUE','FALSE')
                and key(dict(h['proposal'],basis_evidence_ids=[]))==reservation['key']
                for h in report['payload'].get('recent_actions',[])))
            if finished or tick>reservation['expires_tick']:
                del self.access_assignments[actor]
        accepted, suppressed = {}, []
        for actor,task in tasks.items():
            proposal = task['proposal']
            if proposal['action']!='AttemptAccess':
                accepted[actor]=task
                continue
            identity = key(dict(proposal,basis_evidence_ids=[]))
            owners = {peer for peer,r in self.access_assignments.items() if r['key']==identity}
            # A delivered busy report remains evidence even if an issued-task
            # reservation expired. No inspection of another actor's memory.
            for peer,report in self.reports.items():
                pending = report['payload'].get('pending_action')
                if pending and key(dict(pending['proposal'],basis_evidence_ids=[]))==identity:
                    owners.add(peer)
            if owners-{actor}:
                suppressed.append({'actor':actor,'proposal':copy.deepcopy(proposal),
                                   'reason':'Comparable access task already issued to another worker or reported busy'})
                continue
            accepted[actor]=task
            if actor not in self.access_assignments or self.access_assignments[actor]['key']!=identity:
                from packages.contracts.research_catalog import PUBLIC_CATALOG
                duration=PUBLIC_CATALOG['methods'][proposal['method']]['duration']
                self.access_assignments[actor]={'key':identity,'issued_tick':tick,
                    'expires_tick':tick+2*(1+self.config.communication.extra_delay)+duration+self.config.team.claim_ttl}
        return accepted,suppressed

    def admit_swarm(self, memory, proposal, tick):
        """Research access intents settle using delivered claims, never a census.

        This gate is shared by scripted and provider proposals. Waiting costs
        native ticks and transport copies. Manual exploration is handled outside.
        """
        if proposal["action"] != "AttemptAccess":
            self.claim_intents.pop(memory.actor, None)
            self.claim_started.pop(memory.actor, None)
            return proposal
        resource = key(dict(proposal, basis_evidence_ids=[]))
        previous = self.claim_intents.get(memory.actor)
        if previous is None or key(dict(previous, basis_evidence_ids=[])) != resource:
            self.claim_started[memory.actor] = tick
        self.claim_intents[memory.actor] = copy.deepcopy(proposal)
        # Transport has one native tick of base delay, plus configured impairment.
        if tick - self.claim_started[memory.actor] < 1 + self.config.communication.extra_delay:
            return ActionProposal(action="Sleep", rationale="Announcing access intent before its claim can be delivered").model_dump()
        claimants = {memory.actor}
        for message in memory.inbox:
            if message["kind"] == "claim" and tick - message["created_tick"] <= self.config.team.claim_ttl:
                remote = message["payload"]["proposal"]
                if key(dict(remote, basis_evidence_ids=[])) == resource:
                    claimants.add(message["sender"])
        if min(claimants) != memory.actor:
            return ActionProposal(action="Sleep", rationale="A delivered peer claim wins this local access contest").model_dump()
        return proposal

    def options(self, memory, tick, record=False):
        options = candidates(memory)
        if self.config.scenario.research and self.config.cognition.provider != "scripted":
            # LLM inputs get mechanical eligibility, never a programmed strategy.
            return options
        if self.config.cognition.scripted_policy == "legacy":
            return options
        view = memory.public_view({"target_names": self.config.scenario.targets,
            "requirements": self.config.scenario.mission.model_dump() if self.config.scenario.mission else {}}, {})
        policy = self.baselines[memory.actor] if record else copy.deepcopy(self.baselines[memory.actor])
        ranked, trace = policy.rank(view, options, tick)
        if record:
            self.decisions[memory.actor] = trace
        return ranked

    def coordinator_view(self, deliveries, tick):
        self.coordinator_tick = tick
        self.coordinator_inbox.extend(deliveries)
        for m in deliveries:
            if m["kind"] == "report":
                self.reports[m["sender"]] = m
                for h in m["payload"].get("recent_actions", []):
                    if h.get("outcome") == "TRUE" and h.get("valid"):
                        # A successful scan/exploit belongs to its reporting
                        # actor. It cannot complete another actor's scan cache
                        # or session prerequisites for the same target.
                        self.finished.add(f"{m['sender']}:{key(h['proposal'])}")
        return {"role": "coordinator", "tick": tick, "workers": self.actors, "delivered_reports": list(self.reports.values()), "completed_action_keys": sorted(self.finished)}

    def scripted_assignments(self):
        chosen = set()
        result = {}
        pool = []
        # The programmed leader can use the reports it has already received
        # even when forwarding those reports would exceed a worker's belief TTL.
        # This is a coordination heuristic, never a native access prohibition.
        reported_names, reported_owners = {}, {}
        if self.config.scenario.research and self.config.cognition.scripted_policy != 'fixed_workflow':
            tick = getattr(self, 'coordinator_tick', max((r['created_tick'] for r in self.reports.values()),default=0))
            for report in self.reports.values():
                for record in report['payload'].get('research_evidence',[]):
                    for lead in ([record['lead']] if record.get('lead') else []) + record.get('leads',[]):
                        if lead.get('address') and lead.get('hostname'):
                            reported_names[lead['address']] = lead['hostname']
                if tick-report['created_tick']<=self.config.team.claim_ttl:
                    for session in report['payload'].get('sessions',[]):
                        if session['active']:
                            reported_owners.setdefault(session.get('hostname'),set()).add(report['sender'])
        for report in self.reports.values():
            for p in report["payload"].get("candidates", []):
                if "belief_epoch" in report["payload"] or f"{report['sender']}:{key(p)}" not in self.finished:
                    pool.append((p, report))
        if self.config.cognition.scripted_policy == "legacy":
            pool.sort(key=lambda pair: (stage(pair[0]), key(pair[0])))
        else:
            # Ordering is supplied by a worker in an actually delivered report.
            # The coordinator has no access to that worker's live tracker.
            pool.sort(key=lambda pair: (pair[1]["payload"].get("candidates", []).index(pair[0]), stage(pair[0]), key(pair[0])))
        for actor in self.actors:
            recipient_report = self.reports.get(actor)
            if recipient_report and recipient_report["payload"].get("pending_action"):
                continue
            controllers = [s for s in recipient_report["payload"].get("sessions", []) if s["active"] and s["controller"]] if recipient_report else []
            if not controllers:
                continue
            for p, report in pool:
                if p['action'] in ('AttemptAccess','Probe','DiscoverNetworkServices'):
                    owners = reported_owners.get(reported_names.get(p.get('target'),p.get('target')),set())
                    if owners and actor not in owners:
                        continue
                if self.config.cognition.scripted_policy != "legacy" and report["sender"] != actor:
                    # A frontier's source-dependent rank belongs to its sender.
                    # Delivered intel still lets recipients propose their own scan.
                    continue
                k = key(p)
                collision_key = key(dict(p, basis_evidence_ids=[])) if self.config.scenario.research else k
                if collision_key in chosen:
                    continue
                # Sessions/privileges/caches cannot be delegated. Only discovery
                # and rescanning a delivered address can move between workers.
                if p["action"] in ["PrivilegeEscalate", "ExploitRemoteService", "EstablishPivot"] and report["sender"] != actor:
                    continue
                if "belief_epoch" not in recipient_report["payload"] and f"{actor}:{k}" in self.finished:
                    continue
                chosen.add(collision_key)
                # Preserve a worker's selected pivot. Delegating an address
                # cannot transfer a source session belonging to another actor.
                sid = p.get("session", 0) if report["sender"] == actor else controllers[0]["id"]
                result[actor] = {"proposal": dict(p, session=sid), "evidence_ids": report["evidence_ids"], "origin": report["sender"]}
                if self.config.scenario.research:
                    # Forward only progress actually delivered to the leader.
                    # Keep the original report clock; relaying cannot refresh it.
                    result[actor]['coordination_reports'] = self.reported_progress(actor)
                break
        return result

    def reported_progress(self, actor):
        return [{'sender':peer['sender'],'created_tick':peer['created_tick'],
                 'reported_sessions':copy.deepcopy(peer['payload'].get('sessions',[]))}
                for peer in self.reports.values() if peer['sender']!=actor]

    def assigned(self, memory, tick):
        """Mechanical task validation; never a programmed recommendation."""
        tasks = [m for m in memory.inbox if m['kind'] == 'assignment'
                 and tick - m['created_tick'] <= self.config.team.claim_ttl]
        if not tasks:
            return ActionProposal(action='Sleep', rationale='Waiting for a delivered coordinator assignment').model_dump()
        task = tasks[-1]['payload']['proposal']
        self.assignments[memory.actor] = task
        task_key = key(dict(task, basis_evidence_ids=[]))
        visible = {r['evidence_id'] for r in memory.research_evidence} | set(memory.evidence_ids())
        matching = any(key(dict(p, basis_evidence_ids=[])) == task_key for p in candidates(memory))
        if matching and set(task.get('basis_evidence_ids', [])) <= visible:
            return copy.deepcopy(task)
        return ActionProposal(action='Sleep', rationale="Assignment's owned prerequisites/evidence are unavailable").model_dump()

    def preferred(self, memory, tick):
        options = self.options(memory, tick, record=True)
        architecture = self.config.team.architecture
        if architecture == "hierarchy":
            if self.config.scenario.research:
                task = self.assigned(memory, tick)
                if task['action'] == 'Sleep':
                    return task
                # Programmed cognition may decline a task it no longer prefers.
                # This is a strategy decision, not the shared admission boundary.
                task_key = key(dict(task, basis_evidence_ids=[]))
                if any(key(dict(p, basis_evidence_ids=[])) == task_key for p in options):
                    return task
                return ActionProposal(action='Sleep', rationale='Programmed worker strategy defers an eligible delivered task').model_dump()
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
                    claim_key = key(dict(m["payload"]["proposal"], basis_evidence_ids=[])) if self.config.scenario.research else m["payload"]["action_key"]
                    claims.setdefault(claim_key, set()).add(m["sender"])
            available = []
            for p in options:
                claim_key = key(dict(p, basis_evidence_ids=[])) if self.config.scenario.research else key(p)
                claimants = claims.get(claim_key, set()) | {memory.actor}
                # Local deterministic tie breaking from delivered claims only.
                if min(claimants) == memory.actor:
                    available.append(p)
            position = {key(p): i for i, p in enumerate(options)}
            def rank(p):
                # Keep technical stage priority while varying local target
                # preference; there is no shared allocator or private blackboard.
                digest = hashlib.sha256(f"{memory.actor}:{key(p)}".encode()).hexdigest()
                return (stage(p), digest) if self.config.cognition.scripted_policy == "legacy" else (position[key(p)], digest)
            available.sort(key=rank)
            options = available
        return options[0] if options else ActionProposal(action="Sleep", rationale="No locally eligible uncompleted action").model_dump()
