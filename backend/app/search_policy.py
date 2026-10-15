"""Bounded receding-horizon search over a worker's observed reachability graph.

Search selects the next missing goal, or an information frontier when no goal
path is known. It does not solve the whole joint mission optimally. Macro edges
optimistically assume an abstract exploit/escalation works; execution remains
subject to the native engine, retries, observation delay and organization.
"""
import copy
import heapq
from itertools import count

from backend.app.baselines import ACTION_COSTS, LocalStateTracker, action_key
from packages.contracts.models import SearchSettings

VERSION = "1.0"
# Ordinal planning penalties, deliberately NOT calibrated probabilities.
EXPOSURE = {"low": 0, "medium": 0.5, "high": 1}


def search_paths(start, edges, goals, settings, time_budget=None):
    """Uniform-cost search with time/score Pareto labels and a fixed node cap.

    Returns a feasible least-score path to any goal if one is found. If the
    deadline excludes all discovered paths, returns the least-late path with
    an explicit warning. A cap means optimality has not been established.
    """
    serial = count()
    queue = [(0, 0, next(serial), start, [])]
    labels = {start: [(0, 0)]}
    expanded, best_late = 0, None
    while queue and expanded < settings.max_expansions:
        score, ticks, _, node, path = heapq.heappop(queue)
        if (score, ticks) not in labels.get(node, []):
            continue
        expanded += 1
        if node in goals:
            budget = time_budget.get(node) if isinstance(time_budget, dict) else time_budget
            result = {"path": path, "score": score, "ticks": ticks,
                      "goal": node, "deadline_feasible": budget is None or ticks <= budget}
            if result["deadline_feasible"]:
                return dict(result, expansions=expanded, truncated=False)
            if best_late is None or (ticks, score) < (best_late["ticks"], best_late["score"]):
                best_late = result
            continue
        for edge in edges.get(node, []):
            new_score, new_ticks = score + edge["score"], ticks + edge["ticks"]
            dest = edge["target"]
            existing = labels.setdefault(dest, [])
            if any(s <= new_score and t <= new_ticks for s, t in existing):
                continue
            existing[:] = [(s, t) for s, t in existing if not (new_score <= s and new_ticks <= t)]
            existing.append((new_score, new_ticks))
            heapq.heappush(queue, (new_score, new_ticks, next(serial), dest, path + [edge]))
    return dict(best_late or {"path": [], "score": 0, "ticks": 0, "goal": None,
                            "deadline_feasible": None}, expansions=expanded, truncated=bool(queue))


class SearchPolicy:
    def __init__(self, settings=None):
        self.settings = SearchSettings.model_validate(settings or {})
        self.tracker = LocalStateTracker()
        self.edges = {}
        self.epoch = None

    def rank(self, view, candidates, tick):
        changes = self.tracker.update(view, tick)
        native = view["native"]
        # Past positive observations remain beliefs after access loss. Every
        # hypothetical continuation rescans; no cache or session is transferred.
        self.epoch = self.tracker.epoch
        # The same persistent edge facts are available in PrivateMemory to all
        # providers. Strategy search is separate from remembering observations.
        facts = view.get("local_state", self.tracker.snapshot())
        self.edges = {(row["source_host"], row["target_address"]): row["belief_epoch"]
                      for row in facts.get("observed_service_edges", [])}
        sessions = [s for s in native.get("sessions", []) if s["active"]]
        source_names = {s["id"]: s["hostname"] for s in sessions if s["controller"]}
        owned = {s["hostname"] for s in sessions}
        privileged = {s["hostname"] for s in sessions if s["privileged"]}
        mission = view.get("mission", {})
        requirements = mission.get("requirements") or {}
        goals = set(mission.get("target_names", []))
        for objective in requirements.get("objectives", []):
            goals.update(objective.get("targets", []))
            goals.update(objective.get("requires_privileged_hosts", []))
        missing = goals - privileged
        # Mapping comes from the shared tracker (self observations); delivered
        # reports may supply a hostname, but never native exploit eligibility.
        names = dict(self.tracker.address_names)
        for host_id, record in view.get("reported_hosts", {}).items():
            fields = record.get("fields", {})
            name = fields.get("System info", {}).get("Hostname")
            if name:
                for iface in fields.get("Interface", []):
                    ip = str(iface.get("IP Address", ""))
                    if ip in native.get("known", {}).get("ip_address", []):
                        names.setdefault(ip, name)
        def host(target):
            return names.get(str(target), str(target))
        def clue(target):
            result = {}
            for records in (view.get("reported_hosts", {}), view.get("hosts", {})):
                result = records.get(str(target), {}).get("fields", {}).get("Route clue", result)
            return result
        def acquisition(target, first=None, source=None):
            dest = host(target)
            assessment = clue(target)
            label = first["action"] if first else "DiscoverNetworkServices"
            service_ticks = assessment.get("estimated_exploit_ticks", ACTION_COSTS["ExploitRemoteService"])
            root_hint = assessment.get("service_account_hint") == "privileged service"
            goal = dest in missing
            steps = []
            def step(action, destination, ticks):
                steps.append({"action": action, "target": destination, "source_host": source,
                              "estimated_ticks": ticks, "optimistic": action != label or first is None})
            if label == "DiscoverRemoteSystems":
                step(label, target, 1)
                return steps, 1, 0
            if label == "DiscoverNetworkServices":
                step(label, target, 1)
            if label in ("DiscoverNetworkServices", "ExploitRemoteService"):
                step("ExploitRemoteService", target, service_ticks)
                if not root_hint or not goal:
                    step("PrivilegeEscalate", dest, 2)
            elif label == "PrivilegeEscalate":
                step(label, target, 2)
            if (not goal or label == "EstablishPivot") and native.get("pivot_enabled"):
                step("EstablishPivot", dest, 2)
            exposure = EXPOSURE.get(assessment.get("route_sensor_exposure"), 0.5)
            risk = exposure * self.settings.risk_weight if any(s["action"] == "ExploitRemoteService" for s in steps) else 0
            return steps, sum(s["estimated_ticks"] for s in steps), risk

        graph = {}
        for source, target in sorted(self.edges):
            dest = host(target)
            if dest in owned or source == dest:
                continue
            steps, ticks, risk = acquisition(target, source=source)
            stale = self.edges[(source, target)] != self.epoch
            graph.setdefault(source, []).append({"target": dest, "steps": steps,
                                                "ticks": ticks, "score": ticks + risk + (self.settings.unknown_edge_penalty if stale else 0),
                                                "requires_revalidation": True, "observed_in_prior_epoch": stale})
        deadline = requirements.get("deadline_tick")
        # Full hold reserve is conservative: team progress is not given to us.
        hold = requirements.get("hold_ticks", 0)
        budget = None if deadline is None else deadline - tick - hold
        goal_budgets = {g: budget for g in missing}
        for objective in requirements.get("objectives", []):
            own_deadline = objective.get("deadline_tick")
            if own_deadline is None:
                continue
            reserve = max(hold, objective.get("hold_ticks", 1))
            for goal in set(objective.get("targets", [])) | set(objective.get("requires_privileged_hosts", [])):
                if goal in goal_budgets:
                    previous = goal_budgets[goal]
                    goal_budgets[goal] = min(previous, own_deadline - tick - reserve) if previous is not None else own_deadline - tick - reserve
        alternatives = []
        for proposal in candidates:
            label, target, sid = action_key(proposal)
            source = source_names.get(sid)
            dest = host(target)
            steps, ticks, risk = acquisition(target, proposal, source)
            failures = self.tracker.failures.get(action_key(proposal), 0)
            scanned = bool(native.get("scan_cache", {}).get(str(sid), {}).get(str(target), []))
            unknown = label == "DiscoverNetworkServices" and (source, str(target)) not in self.edges
            penalty = failures * self.settings.failure_penalty + (self.settings.unknown_edge_penalty if unknown else 0)
            if label == "ExploitRemoteService" and proposal.get("rationale", "").startswith("Own service evidence is aged"):
                penalty += self.settings.unknown_edge_penalty
            remaining_budget = {g: None if b is None else b - ticks for g,b in goal_budgets.items()}
            result = search_paths(dest, graph if native.get("pivot_enabled") else {}, missing, self.settings, remaining_budget) if label != "DiscoverRemoteSystems" else {
                "goal": None, "ticks": 0, "score": 0, "path": [], "expansions": 0, "truncated": False, "deadline_feasible": None}
            has_goal = result["goal"] is not None
            plan = steps + [step for edge in result["path"] for step in edge["steps"]]
            total_ticks = ticks + result["ticks"]
            applicable_budget = goal_budgets.get(result["goal"], budget)
            feasible = applicable_budget is None or total_ticks <= applicable_budget
            score = ticks + risk + penalty + result["score"]
            # Known goal paths outrank pure information frontiers. Among paths,
            # deadline feasibility precedes risk-adjusted cost. No probability
            # of success or hidden ACL is used to declare a path guaranteed.
            rank = (0 if has_goal else 1, 0 if feasible else 1,
                    score if feasible else total_ticks, score, str(target), sid)
            alternatives.append({"proposal": copy.deepcopy(proposal), "rank": list(rank),
                "observed_goal": dest in missing, "observed_failures": failures,
                "estimated_action_ticks": steps[0]["estimated_ticks"] if steps else 0,
                "estimated_remaining_ticks": total_ticks - (steps[0]["estimated_ticks"] if steps else 0),
                "observed_service_evidence": scanned, "observed_route_clue": copy.deepcopy(clue(target)),
                "reason": "Search to the next observed missing goal" if has_goal else "Explore an observed information frontier",
                "plan": plan[:24], "plan_steps_omitted": max(0, len(plan)-24),
                "search_goal": result["goal"], "estimated_total_ticks": total_ticks,
                "planning_score": score, "deadline_feasible": feasible,
                "unknown_first_connection": unknown, "search_expansions": result["expansions"],
                "search_truncated": result["truncated"]})
        alternatives.sort(key=lambda a: tuple(a["rank"]))
        holding = bool(goals) and not missing
        if holding:
            alternatives = []
        trace = {"policy": "local_search", "version": VERSION, "tick": tick, "actor": view["actor"],
                 "state_change": changes, "own_missing_goals": sorted(missing),
                 "status": "holding_own_goals" if holding else "searching_observed_graph" if alternatives else "no_eligible_action",
                 "candidate_count": len(alternatives), "alternatives": alternatives[:12],
                 "omitted_alternatives": max(0, len(alternatives)-12),
                 "search": {"settings": self.settings.model_dump(), "observed_edges": len(self.edges),
                            "deadline_tick": deadline, "conservative_hold_reserve": hold, "time_budget": budget,
                            "goal_time_budgets": goal_budgets,
                            "scope": "next goal or information frontier; optimistic exploit/escalation outcomes; no full-mission optimality"}}
        return [row["proposal"] for row in alternatives], trace
