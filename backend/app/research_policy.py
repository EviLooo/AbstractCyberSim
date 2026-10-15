"""Versioned policies over public rules and recipient-local evidence only.

The fixed controller ignores diagnostic content. The evidence controller uses
disclosed responses/claimed scope, not actual compatibility. The planner searches
small observed prerequisite graphs, with optimistic unknown-condition estimates.
"""
import copy
import heapq

NAMES = ("fixed_workflow", "evidence_controller", "observed_planner")
VERSION = "1.0"


def signature(p):
    return tuple(p.get(k) for k in ("action", "target", "session", "source_host", "method", "probe", "port", "token_ref"))


def describe(name):
    return {"id": name, "version": VERSION, "catalog": "minimal_access_v1",
            "information": "own observations and actually delivered reports",
            "priors": "public durations; notes are fallible; unknown SSH weakness is not confirmed by auth probe",
            "search": "bounded observed prerequisite graphs" if name == "observed_planner" else
                      "evidence-conditioned priorities" if name == "evidence_controller" else "fixed method order and bounded retries",
            "qualification": "optimistic software controller; no global optimality, calibrated probabilities or scientific advantage"}


class ResearchPolicy:
    def __init__(self, name, retry_limit=2, backoff=0):
        if name not in NAMES:
            raise ValueError("Unknown research policy")
        self.name, self.retry_limit, self.backoff = name, retry_limit, backoff
        self.seen, self.completed, self.failures = set(), {}, {}
        self.epoch = None

    def rank(self, view, candidates, tick):
        epoch = view.get("belief_epoch", 0)
        if self.epoch != epoch:
            # Own access loss permits fresh investigation; old evidence remains.
            self.completed, self.failures = {}, {}
            self.epoch = epoch
            self.epoch_started_tick = tick
        for r in view.get("history", []):
            if r.get("belief_epoch", 0) != epoch or r.get("remaining_ticks", 0) or (not r.get("submitted", True) and r.get("lifecycle") != "completed"):
                continue
            identity = (r.get("observed_tick"), repr(r.get("proposal")), r.get("outcome"))
            if identity in self.seen:
                continue
            self.seen.add(identity)
            p, success = r["proposal"], r.get("valid", True) and r.get("outcome") == "TRUE"
            s = signature(p)
            if success:
                self.completed[s] = tick
            elif r.get("outcome") == "FALSE" or not r.get("valid", True):
                count, _ = self.failures.get(s, (0, 0))
                self.failures[s] = count + 1, tick
        native = view["native"]
        goals = set(view.get("mission", {}).get("target_names", []))
        names = {}
        for collection in (view.get("reported_hosts", {}), view.get("hosts", {})):
            for address, h in collection.items():
                names[address] = h["fields"].get("System info", {}).get("Hostname", address)
        records = view.get("research_evidence", [])
        artifact_leads = set()
        for record in records:
            if record.get('kind')!='artifact':
                continue
            for lead in ([record['lead']] if record.get('lead') else []) + record.get('leads',[]):
                if lead.get('address'):
                    artifact_leads.add(lead['address'])
                    if lead.get('hostname'):
                        names.setdefault(lead['address'],lead['hostname'])
        latest = {}
        for r in records:
            k = (r["host"], r.get("source_host"), r.get("probe"), r.get("port"))
            if r.get("kind") == "probe" and (k not in latest or r["observed_tick"] >= latest[k]["observed_tick"]):
                latest[k] = r
        own = {s["hostname"]: s for s in native["sessions"] if s["active"]}
        peer_reports = {}
        for message in view.get("inbox", []):
            if message.get("kind") == "claim" and tick - message["created_tick"] <= view.get("coordination", {}).get("claim_ttl", 5):
                peer_reports[message["sender"]] = message["payload"].get("reported_sessions", [])
            elif message.get('kind')=='assignment':
                for report in message['payload'].get('coordination_reports',[]):
                    if report['sender']!=view.get('actor') and tick-report['created_tick']<=view.get('coordination',{}).get('claim_ttl',5):
                        peer_reports[report['sender']] = report['reported_sessions']
        peer_owned = {s["hostname"] for sessions in peer_reports.values() for s in sessions if s["active"]}
        peer_privileged = {s["hostname"] for sessions in peer_reports.values() for s in sessions if s["active"] and s["privileged"]}
        # Delivered reports are coordination beliefs, never native ownership.
        # Stop duplicating an active peer's branch; loss or expiry reopens it.
        missing = goals - {h for h, s in own.items() if s["privileged"]} - peer_privileged
        scored = []
        for original in candidates:
            p = copy.deepcopy(original)
            s, label = signature(p), p["action"]
            failed, failed_tick = self.failures.get(s, (0, -10000))
            if failed >= self.retry_limit or tick - failed_tick < self.backoff:
                continue
            target, source = p.get("target"), p.get("source_host")
            host = names.get(target, target)
            is_goal = host in missing
            done = self.completed.get(s)
            # Reinspect after own privilege upgrade; root-only notes may appear.
            if done is not None and label == "InspectArtifacts":
                upgrades = [r for r in view.get("history", []) if r["proposal"]["action"] == "PrivilegeEscalate"
                            and r["proposal"].get("target") == target and r.get("outcome") == "TRUE"
                            and r.get("observed_tick", 0) >= done]
                if upgrades:
                    self.completed.pop(s)
                    done = None
            probe = latest.get((target, source, "service_behavior", 80))
            auth = latest.get((target, source, "auth_policy", 22))
            stale = bool(probe and probe.get("stale"))
            web_hypothesis = dict(p, action='AttemptAccess', method='web_rfi', probe=None, port=None, token_ref=None)
            web_failure_tick = self.failures.get(signature(web_hypothesis), (0, -1))[1]
            recheck_import = bool(label=='Probe' and p.get('probe')=='service_behavior' and probe
                                  and probe['response']=='external_import_accepted'
                                  and web_failure_tick>=probe['observed_tick'])
            if done is not None:
                if label == "Probe" and self.name != "fixed_workflow":
                    own_probe = latest.get((target, source, p.get("probe"), p.get("port")))
                    if not own_probe or not own_probe.get("stale") and not recheck_import or not missing or own_probe["response"] in ("timeout", "external_import_refused"):
                        continue
                    if p["probe"] == "auth_policy":
                        weak = dict(p, action="AttemptAccess", method="ssh_weak_auth", probe=None, port=None, token_ref=None)
                        usable_claim = any(r.get("token_ref") in native.get("possessed_tokens", [])
                            and r.get("claimed_scope") == host
                            and not self.failures.get(signature(dict(weak, method="credential_login", token_ref=r.get("token_ref"))))
                            for r in records if r.get("token_ref"))
                        if self.failures.get(signature(weak)) and not usable_claim:
                            # Repeating a password handshake cannot discover a
                            # missing credential or repair a disproved method.
                            continue
                else:
                    continue
            reason = "fixed public workflow"
            priority = 30
            if label == "InspectArtifacts":
                priority = 0
                reason = "Inspect an owned local session for fallible leads and token references"
            elif label == "PrivilegeEscalate":
                priority = -1 if is_goal and self.name!='fixed_workflow' else 1 if is_goal else 4
                reason = "Gain own privilege needed for the goal or a source pivot"
            elif label == "EstablishPivot":
                priority = 5
                reason = "Create an owned source and empty local scan cache"
            elif label == "DiscoverNetworkServices":
                priority = 7 if is_goal else 17
            elif label == "DiscoverRemoteSystems":
                priority = 50
            elif label == "Probe":
                if self.name == "fixed_workflow" or p["probe"] == "connectivity":
                    continue
                if target not in native.get("scan_cache", {}).get(str(p.get("session", 0)), {}):
                    # This controller scans first so a useful diagnostic can
                    # lead immediately to an eligible explicit access attempt.
                    # Mechanical candidates still allow other legal workflows.
                    continue
                observed = latest.get((target, source, p["probe"], p["port"]))
                if observed and not observed.get("stale") and not recheck_import:
                    # A verified peer's source-specific response is evidence,
                    # not an owned scan cache. Rescan prerequisites remain local.
                    continue
                if observed and observed["observed_tick"] >= self.epoch_started_tick and observed["response"] in ("timeout", "external_import_refused"):
                    # A stale negative is still a rejected hypothesis in this
                    # controller. Aging alone is not evidence that a service
                    # was repaired. Own access loss opens a new investigation.
                    continue
                priority = (8 if is_goal else 15) + (p["probe"] == "auth_policy")
                if observed and not recheck_import:
                    # Fresh investigation must not be starved by repeatedly
                    # refreshing a positive result with no usable dependency.
                    priority += 30
                reason = "Diagnose a selected service from this owned source; refresh stale evidence"
            elif label == "AttemptAccess":
                method = p["method"]
                if self.name != "fixed_workflow" and host in peer_owned and host not in own:
                    continue
                if native.get("access_resources", {}).get("remaining", 1) <= 0:
                    continue
                if self.name != "fixed_workflow" and failed:
                    # An unchanged failed method is a disproved local hypothesis,
                    # not an invitation to spend the shared budget again. Own
                    # access loss starts a new epoch; a new token is a new key.
                    continue
                order = {"web_rfi": 0, "ssh_weak_auth": 1, "credential_login": 2}[method]
                priority = (11 if is_goal else 21) + order
                if self.name != "fixed_workflow":
                    if method == "web_rfi":
                        if not probe or probe["response"] != "external_import_accepted" or stale:
                            continue
                        reason = "Current source probe accepts external imports; attempt that explicit method"
                    elif method == "ssh_weak_auth":
                        if not auth or auth["response"] != "password_and_account_token_supported" or auth.get("stale"):
                            continue
                        reason = "Reachable password service; account weakness remains a hypothesis"
                        # Auth policy does not prove password weakness. Prefer
                        # actual provisioning hints or alternative capabilities.
                        hint = any(r.get("kind") == "artifact" and "weak" in r.get("text", "").lower()
                                   and (r.get("lead", {}).get("hostname") == host or r["host"] == host) for r in records)
                        if hint:
                            reason += "; a disclosed provisioning note supports this hypothesis"
                    else:
                        notes = [r for r in records if r.get("token_ref") == p.get("token_ref") and r.get("claimed_scope") == host]
                        if not notes or not auth or auth["response"] != "password_and_account_token_supported" or auth.get("stale"):
                            continue
                        order = -1
                        reason = "Delivered artifact claims this scope; validity remains unverified until login"
                    # Act on a useful fresh result before opening every other
                    # investigation frontier and aging that result away.
                    priority = (6 if is_goal else 13) + order + failed * 3
            else:
                continue
            if self.name!='fixed_workflow' and label in ('DiscoverNetworkServices','Probe','AttemptAccess') and not is_goal and target not in artifact_leads:
                # Investigate disclosed task leads before incidental background
                # discoveries. A fallible note is a priority, not proof of a
                # permitted route or a restriction on the mechanical catalog.
                priority += 10
            p["rationale"] = reason
            cost = native["catalog"]["methods"][p["method"]]["duration"] if label == "AttemptAccess" else native["catalog"]["probes"][p["probe"]]["duration"] if label == "Probe" else native["catalog"].get("local_actions", {}).get(label, {}).get("duration", 2)
            scored.append((priority, str(signature(p)), p, {"proposal": p, "observed_goal": is_goal,
                          "failures": failed, "observed_failures": failed, "estimated_action_ticks": cost,
                          "estimated_remaining_ticks": 0, "reason": reason, "priority": priority}))
        scored.sort(key=lambda row: row[:2])
        plans = self._plans(view, [r[2] for r in scored], latest, names, missing, candidates) if self.name == "observed_planner" else []
        if plans:
            positions = {signature(plan["next_action"]): (0 if plan["observed_goal"] else 1, plan["estimated_ticks"])
                         for plan in reversed(plans)}
            # Ownership maintenance is a prerequisite shared with all methods.
            scored.sort(key=lambda r: (-1, r[0]) if r[2]["action"] in ("InspectArtifacts", "PrivilegeEscalate", "EstablishPivot")
                        else positions.get(signature(r[2]), (2, r[0])))
        return [r[2] for r in scored], {"policy": self.name, "version": VERSION, "tick": tick,
                "status": "ranked" if scored else "no_private_frontier",
                "own_missing_goals": sorted(goals - {h for h, s in own.items() if s["privileged"]}),
                "believed_team_missing_goals": sorted(missing),
                "state_change": {"belief_epoch": epoch},
                "candidate_count": len(candidates), "alternatives": [r[3] for r in scored[:12]],
                "plans": plans, "limits": {"max_graph_expansions": 128},
                "qualification": describe(self.name)["qualification"]}

    def _plans(self, view, options, latest, names, missing, frontiers):
        """Uniform-cost paths in finite source/target prerequisite graphs.

        Future method validity and privilege success are optimistic assumptions.
        Graphs contain no hidden route; blocked evidence excludes a method.
        """
        native, plans = view["native"], []
        catalog = native["catalog"]
        for scan in (p for p in frontiers if p["action"] == "DiscoverNetworkServices"):
            target, source, sid = scan["target"], scan["source_host"], str(scan["session"])
            cached = target in native["scan_cache"].get(sid, {})
            if not cached and not any(signature(p)==signature(scan) for p in options):
                continue
            edges = {"start": [("scanned", 0 if cached else 1, None if cached else scan, [])], "scanned": []}
            for method, data in catalog["methods"].items():
                kind = "service_behavior" if method == "web_rfi" else "auth_policy"
                record = latest.get((target, source, kind, data["port"]))
                if record and not record.get("stale") and record["response"] in ("timeout", "external_import_refused"):
                    continue
                tokens = [None]
                if method == "credential_login":
                    tokens = [r["token_ref"] for r in view["research_evidence"] if r.get("token_ref") in native.get("possessed_tokens", [])
                              and r.get("claimed_scope") == names.get(target, target)]
                for token in dict.fromkeys(tokens):
                    probe = next((p for p in options if p["action"] == "Probe" and p["target"] == target and p["source_host"] == source and p["probe"] == kind), None)
                    attempt = next((p for p in options if p["action"] == "AttemptAccess" and p["target"] == target and p["source_host"] == source and p["method"] == method and p.get("token_ref") == token), None)
                    unknown = ["method compatibility", "privilege escalation success"]
                    diagnosed = bool(record and not record.get("stale"))
                    if cached and (attempt is None or not diagnosed and probe is None):
                        continue
                    node = method + str(token)
                    edges["scanned"].append((node, 0 if diagnosed else catalog["probes"][kind]["duration"], None if diagnosed else probe, unknown))
                    edges[node] = [("access", data["duration"], attempt, unknown)]
            edges["access"] = [("privileged", 2, None, ["privilege escalation success"])]
            queue, count, best = [(0, 0, "start", [], [])], 0, {}
            while queue and count < 128:
                cost, _, node, path, unknown = heapq.heappop(queue)
                if node in best:
                    continue
                best[node], count = cost, count + 1
                if node == "privileged":
                    if path:
                        plans.append({"source": source, "target": target, "observed_goal": names.get(target, target) in missing,
                            "estimated_ticks": cost, "next_action": path[0], "path": path,
                            "unknown_conditions": sorted(set(unknown)), "expansions": count,
                            "estimate": "optimistic observed graph; no hidden route or probability"})
                    break
                for index, (to, weight, action, assumptions) in enumerate(edges.get(node, [])):
                    heapq.heappush(queue, (cost + weight, count * 100 + index, to,
                                         path + ([action] if action else []), unknown + assumptions))
        return sorted(plans, key=lambda p: (not p["observed_goal"], p["estimated_ticks"], p["target"]))[:32]
