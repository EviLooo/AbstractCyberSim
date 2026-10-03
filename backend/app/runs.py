"""Tick-boundary control, private-agent pipeline, and saved replay evidence."""
import asyncio
import copy
import hashlib
import uuid
from backend.app.bridge import EngineBridge
from backend.app.evaluation import metrics
from backend.app.knowledge import PrivateMemory
from backend.app.policies import Organization, candidates, key
from backend.app.providers import BudgetExceeded, Cognition
from backend.app.settings import ROOT
from backend.app.storage import digest, now
from backend.app.transport import MessageBus

TERMINAL = {"completed", "stopped", "errored", "interrupted"}


def source_fingerprint():
    paths = []
    for folder in ["backend", "packages", "prompts", "engine"]:
        paths.extend(p for p in (ROOT / folder).rglob("*") if p.is_file() and p.suffix in [".py", ".txt", ".json", ".md"])
    return digest({str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)})


class Run:
    def __init__(self, config, store):
        config = config.model_copy(deep=True)
        self.config, self.store = config, store
        self.id = uuid.uuid4().hex
        self.lock = asyncio.Lock()
        self.pause_requested = False
        self.stop_requested = False
        self.task = None
        self.frames = []
        self.meta = {"id": self.id, "name": config.name, "status": "initializing", "purpose": config.purpose, "manual_intervention": False, "tick": 0, "architecture": config.team.architecture, "workers": config.team.workers, "reasoners": config.team.workers + int(config.team.architecture == "hierarchy"), "created_at": now(), "updated_at": now(), "termination_reason": None, "world_id": None, "config_hash": digest(config.model_dump()), "code_fingerprint": source_fingerprint()}
        condition = config.model_dump()
        for field in ["name", "purpose", "schema_version"]:
            condition.pop(field)
        condition["team"].pop("architecture")
        condition["code_fingerprint"] = self.meta["code_fingerprint"]
        # Transport topology is the treatment; identical numeric conditions pair.
        self.meta["condition_hash"] = digest(condition)
        self.directory = store.path(self.id)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.store.write_json(self.directory / "config.json", config.model_dump())
        self.store.update(self.meta)
        self.engine = EngineBridge(self.directory / "engine.stderr.log")
        self.cognition = Cognition(config.cognition, self.directory / "provider-transcripts.jsonl")

    async def initialize(self):
        try:
            versions = await self.engine.start()
            result = await self.engine.call("create", config=self.config.model_dump())
            self.actors = result["actors"]
            self.memory = {a: PrivateMemory(a) for a in self.actors}
            self.bus = MessageBus(self.config.communication, self.actors, self.config.team.architecture)
            self.organization = Organization(self.config, self.actors)
            for a in self.actors:
                self.memory[a].observe(result["observations"][a], result["views"][a])
            self.meta.update(status="ready", world_id=result["world"]["world_id"])
            self.store.write_json(self.directory / "world.json", result.pop("world"))
            self.store.write_json(self.directory / "manifest.json", {"schema_version": "1.0", "versions": versions, "config_hash": self.meta["config_hash"], "code_fingerprint": self.meta["code_fingerprint"], "prompt_hashes": self.cognition.prompt_hashes, "world_id": self.meta["world_id"], "qualification": "Software prototype; enterprise research calibration pending"})
            self.persist(result)
        except BaseException as exc:
            self.meta.update(status="errored", termination_reason="initialization_error", error=str(exc))
            self.store.update(self.meta)
            await self.engine.close()
            raise
        return self.meta

    def persist(self, result):
        frame = dict(result, status=self.meta["status"], messages=self.bus.snapshot(), private_views={a: self.memory[a].public_view(self.mission(), self.budget()) for a in self.actors}, coordinator={"delivered_reports": copy.deepcopy(self.organization.reports), "assignments": copy.deepcopy(self.organization.assignments)} if self.config.team.architecture == "hierarchy" else None, cognition=self.cognition.summary(), manual_intervention=self.meta["manual_intervention"])
        self.frames.append(frame)
        self.store.save_frame(self.id, frame)
        self.meta.update(tick=result["tick"], updated_at=now(), metrics=metrics(self.frames, self.cognition.summary()))
        self.store.update(self.meta)

    def budget(self):
        return {"remaining_team_tokens": max(0, self.config.cognition.max_team_tokens - self.cognition.used)}

    def mission(self):
        return {"objective": "privileged_access_all", "target_names": self.config.scenario.targets, "architecture": self.config.team.architecture, "worker_count": self.config.team.workers}

    async def bridge_messages(self, deliveries):
        for actor in self.actors:
            messages = deliveries.get(actor, [])
            self.memory[actor].receive(messages)
            if not self.config.communication.verified_intel:
                continue
            for m in messages:
                # Origin is encoded in engine-generated evidence ID and checked
                # against engine registry. A coordinator may relay only received
                # evidence IDs (provider gateway restriction).
                groups = {}
                for eid in m["evidence_ids"]:
                    origin = eid.split(":", 1)[0]
                    if origin in self.actors:
                        groups.setdefault(origin, []).append(eid)
                for origin, ids in groups.items():
                    update = await self.engine.call("ingest_intel", sender=origin, recipient=actor, evidence_ids=ids)
                    self.memory[actor].view = update["view"]
                    self.store.event(self.id, {"type": "intel_delivery", "tick": m["resolved_tick"], "message_id": m["id"], "recipient": actor, "origin": origin, "evidence_ids": update["accepted_evidence"], "address_fragment": update["address_fragment"]})

    async def advance(self, overrides=None):
        async with self.lock:
            if self.meta["status"] in TERMINAL:
                raise ValueError("This run is closed; use saved replay or create a new run")
            overrides = overrides or {}
            if set(overrides) - set(self.actors):
                raise ValueError("Override contains unknown actors")
            if overrides and self.config.purpose != "exploration":
                raise ValueError("Manual actions are disabled in evaluation runs")
            if overrides:
                self.meta["manual_intervention"] = True
                self.store.event(self.id, {"type": "manual_intervention", "tick": self.meta["tick"] + 1, "overrides": overrides})
            tick = self.meta["tick"] + 1
            try:
                deliveries, delivery_events = self.bus.deliver(tick)
                await self.bridge_messages(deliveries)
                if self.config.team.architecture == "hierarchy":
                    coord_view = self.organization.coordinator_view(deliveries.get("Coordinator", []), tick)
                    coord_view["mission"] = self.mission()
                    defaults = self.organization.scripted_assignments()
                    tasks = await self.cognition.coordinator(coord_view, defaults) if coord_view["delivered_reports"] else {}
                    for actor, task in tasks.items():
                        self.bus.enqueue("Coordinator", [actor], "assignment", task, task["evidence_ids"], tick)
                proposals = {}
                organization_rejections = {}
                for actor in self.actors:
                    memory = self.memory[actor]
                    preferred = self.organization.preferred(memory, tick)
                    if actor in overrides:
                        proposals[actor] = overrides[actor]
                    else:
                        view = memory.public_view(self.mission(), self.budget())
                        view["eligible_candidates"] = candidates(memory)
                        proposed = await self.cognition.worker(actor, view, preferred)
                        if self.config.team.architecture == "hierarchy" and proposed["action"] != "Sleep" and key(proposed) != key(preferred):
                            organization_rejections[actor] = {"proposal": proposed, "rejection": "Hierarchy worker action does not match a locally eligible delivered assignment"}
                            proposals[actor] = {"action": "Sleep", "rationale": "Organization gateway rejected an unassigned action"}
                        else:
                            proposals[actor] = proposed
                suppressed = []
                if self.config.schedule.mode == "team_cap_one":
                    chosen = (tick - 1) % len(self.actors)
                    for index, actor in enumerate(self.actors):
                        if index != chosen:
                            suppressed.append({"actor": actor, "proposal": proposals[actor]})
                            proposals[actor] = {"action": "Sleep", "rationale": "Neutral one-action team capacity limit"}
                result = await self.engine.call("step", proposals=proposals)
                for record in result["actions"]:
                    if record["actor"] in organization_rejections:
                        record.update(organization_rejections[record["actor"]], valid=False)
                    self.memory[record["actor"]].history.append(record)
                for actor in self.actors:
                    memory = self.memory[actor]
                    memory.observe(result["observations"][actor], result["views"][actor])
                    if self.config.team.architecture == "hierarchy":
                        report = {"candidates": candidates(memory), "recent_actions": memory.history[-4:], "known": memory.view["known"], "sessions": memory.view["sessions"]}
                        self.bus.enqueue(actor, ["Coordinator"], "report", report, memory.evidence_ids(), tick)
                    elif self.config.team.architecture == "swarm":
                        self.bus.enqueue(actor, self.bus.neighbors(actor), "claim", {"action_key": key(proposals[actor]), "proposal": proposals[actor], "known": memory.view["known"]}, memory.evidence_ids(), tick)
                result.update(delivery_events=delivery_events, suppressed_proposals=suppressed)
                reason = "mission_success" if result["score"]["mission_success"] else "native_done" if result["native_done"] else "tick_limit" if tick >= self.config.schedule.max_ticks else None
                if reason:
                    self.meta.update(status="completed", termination_reason=reason)
                elif self.meta["status"] != "running":
                    self.meta["status"] = "paused"
                self.persist(result)
                if reason:
                    await self.engine.close()
                return self.meta
            except BaseException as exc:
                self.meta.update(status="completed" if isinstance(exc, BudgetExceeded) else "errored", termination_reason="token_budget" if isinstance(exc, BudgetExceeded) else "runtime_error", error=str(exc), updated_at=now())
                self.meta["metrics"] = metrics(self.frames, self.cognition.summary())
                self.store.event(self.id, {"type": "error", "tick": tick, "message": str(exc), "cognition": self.cognition.summary()})
                self.store.update(self.meta)
                await self.engine.close()
                if isinstance(exc, BudgetExceeded):
                    return self.meta
                raise

    async def loop(self):
        try:
            while not self.pause_requested and not self.stop_requested and self.meta["status"] not in TERMINAL:
                await self.advance()
                await asyncio.sleep(0.4)
        except Exception:
            # advance already records the error and closes the native process.
            pass
        finally:
            if self.meta["status"] not in TERMINAL:
                if self.stop_requested:
                    self.meta.update(status="stopped", termination_reason="user_stop")
                    await self.engine.close()
                else:
                    self.meta["status"] = "paused"
                self.meta["updated_at"] = now()
                self.store.update(self.meta)

    def start(self):
        if self.meta["status"] in TERMINAL or self.meta["status"] == "running":
            raise ValueError("Run cannot be started in its current state")
        self.pause_requested = self.stop_requested = False
        self.meta["status"] = "running"
        self.store.update(self.meta)
        self.task = asyncio.create_task(self.loop())
        return self.meta

    async def pause(self):
        self.pause_requested = True
        if self.task and not self.task.done():
            await self.task
        return self.meta

    async def stop(self):
        self.stop_requested = True
        await self.pause()
        async with self.lock:
            if self.meta["status"] not in TERMINAL:
                self.meta.update(status="stopped", termination_reason="user_stop", updated_at=now())
                self.store.update(self.meta)
            await self.engine.close()
        return self.meta


class RunManager:
    def __init__(self, store):
        self.store = store
        self.live = {}
        self.create_lock = asyncio.Lock()

    async def create(self, config):
        async with self.create_lock:
            active = sum(r.meta["status"] not in TERMINAL for r in self.live.values())
            if active >= 4:
                raise ValueError("Four live runs already exist; stop one before creating another")
            run = Run(config, self.store)
            self.live[run.id] = run
            await run.initialize()
            return run.meta

    def get(self, run_id):
        if run_id not in self.live:
            self.store.get(run_id)
            raise ValueError("Saved run supports replay only; create a fresh run to control the engine")
        return self.live[run_id]

    async def close(self):
        await asyncio.gather(*(r.stop() for r in self.live.values()), return_exceptions=True)
