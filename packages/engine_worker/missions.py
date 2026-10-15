"""Tick-based objective monitor. Pure Python, imported only by the native worker.

Requirements describe privileged host access, never report labels or task IDs.
Counters are sampled once after the entire native tick, including end-turn
actions. A sampled break resets progress, including previously completed stages.
"""
import copy


def resolve_mission(targets, settings=None):
    settings = settings or {}
    return {"version": "1.0", "targets": list(targets),
            "hold_ticks": settings.get("hold_ticks", 1),
            "deadline_tick": settings.get("deadline_tick"),
            "objectives": copy.deepcopy(settings.get("objectives") or [])}


class MissionTracker:
    def __init__(self, targets, settings=None):
        self.definition = resolve_mission(targets, settings)
        self.objectives = self.definition["objectives"] or [{"id": "all_targets",
            "targets": list(targets), "requires_privileged_hosts": [],
            "hold_ticks": 1, "deadline_tick": None}]
        self.progress = {o["id"]: {"hold_ticks": 0, "best_hold_ticks": 0,
            "reset_count": 0, "completed": False} for o in self.objectives}
        self.hold = self.best = self.resets = 0
        self.failure = None
        self.tick = -1
        self.snapshot = None

    def update(self, tick, privileged_hosts):
        if tick == self.tick:
            return copy.deepcopy(self.snapshot)
        if self.tick >= 0 and tick != self.tick + 1:
            raise ValueError("Mission monitor requires consecutive world ticks")
        self.tick = tick
        access = set(privileged_hosts)
        events, stages = [], []
        for objective in self.objectives:
            state = self.progress[objective["id"]]
            previous = state["hold_ticks"]
            missing_targets = sorted(set(objective["targets"]) - access)
            missing_prerequisites = sorted(set(objective.get("requires_privileged_hosts", [])) - access)
            satisfied = not missing_targets and not missing_prerequisites
            state["hold_ticks"] = min(previous + 1, objective["hold_ticks"]) if satisfied and tick > 0 else 0
            if previous and not satisfied:
                state["reset_count"] += 1
                events.append({"type": "objective_hold_reset", "objective": objective["id"], "tick": tick,
                    "previous_hold_ticks": previous, "missing_targets": missing_targets,
                    "missing_prerequisites": missing_prerequisites})
            completed = state["hold_ticks"] >= objective["hold_ticks"]
            if completed and not state["completed"]:
                events.append({"type": "objective_satisfied", "objective": objective["id"], "tick": tick})
            state["completed"] = completed
            state["best_hold_ticks"] = max(state["best_hold_ticks"], state["hold_ticks"])
            deadline = objective.get("deadline_tick")
            missed = deadline is not None and tick >= deadline and not completed
            if missed and not self.failure:
                self.failure = {"reason": "objective_deadline", "objective": objective["id"], "tick": tick, "deadline_tick": deadline}
            stages.append(dict(copy.deepcopy(objective), **state, satisfied=satisfied,
                required_hold_ticks=objective["hold_ticks"],
                missing_targets=missing_targets, missing_prerequisites=missing_prerequisites,
                status="deadline_missed" if missed else "complete" if completed else "holding" if satisfied and tick else "blocked" if missing_prerequisites else "awaiting_access"))
        all_access = set(self.definition["targets"]) <= access
        ready = all_access and all(s["completed"] for s in stages)
        previous_hold = self.hold
        self.hold = min(self.hold + 1, self.definition["hold_ticks"]) if ready and tick > 0 else 0
        if previous_hold and not ready:
            self.resets += 1
            events.append({"type": "mission_hold_reset", "tick": tick, "previous_hold_ticks": previous_hold})
        self.best = max(self.best, self.hold)
        deadline = self.definition["deadline_tick"]
        success = self.hold >= self.definition["hold_ticks"] and not self.failure
        if deadline is not None and tick >= deadline and not success and not self.failure:
            self.failure = {"reason": "mission_deadline", "tick": tick, "deadline_tick": deadline}
        if self.failure and (not self.snapshot or not self.snapshot.get("failure")):
            events.append(dict(self.failure, type="mission_failed"))
        if success and (not self.snapshot or not self.snapshot["success"]):
            events.append({"type": "mission_completed", "tick": tick})
        self.snapshot = {"definition": copy.deepcopy(self.definition), "tick": tick,
            "hold_ticks": self.hold, "required_hold_ticks": self.definition["hold_ticks"],
            "best_hold_ticks": self.best, "reset_count": self.resets,
            "deadline_tick": deadline, "remaining_ticks": max(0, deadline - tick) if deadline is not None else None,
            "all_target_access": all_access, "objectives": stages,
            "status": "failed" if self.failure else "complete" if success else "holding" if ready else "awaiting_access",
            "success": success, "failure": copy.deepcopy(self.failure), "events": events}
        return copy.deepcopy(self.snapshot)
