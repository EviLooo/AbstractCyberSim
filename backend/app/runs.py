"""Tick-boundary control, private-agent pipeline, and saved replay evidence."""
import asyncio
import copy
import hashlib
import uuid
from types import SimpleNamespace
from backend.app.bridge import EngineBridge
from backend.app.beliefs import perceived_action
from backend.app.evaluation import metrics
from backend.app.knowledge import PrivateMemory
from backend.app.policies import Organization, candidates, key, ORGANIZATION_VERSION
from backend.app.providers import BudgetExceeded, Cognition, ProviderRefusal, InvalidDecision, ContextExceeded
from backend.app.settings import ROOT
from backend.app.storage import digest, now
from backend.app.transport import MessageBus
from backend.app.baselines import describe_policy
from backend.app.diagnostics import structure, reduce_decisions
from packages.contracts.module_registry import compile_modules

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
        self.modules = compile_modules(config)
        self.id = uuid.uuid4().hex
        self.lock = asyncio.Lock()
        self.pause_requested = False
        self.stop_requested = False
        self.task = None
        self.frames = []
        self.meta = {"id": self.id, "name": config.name, "status": "initializing", "purpose": config.purpose, "manual_intervention": False, "tick": 0, "architecture": config.team.architecture, "workers": config.team.workers, "reasoners": config.team.workers + int(config.team.architecture == "hierarchy"), "created_at": now(), "updated_at": now(), "termination_reason": None, "world_id": None, "config_hash": digest(config.model_dump()), "code_fingerprint": source_fingerprint()}
        self.meta["profile"] = config.scenario.profile
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
        self.engine = EngineBridge(self.directory / "engine.stderr.log", config.scenario.profile)
        self.cognition = Cognition(config.cognition, self.directory / "provider-transcripts.jsonl")

    async def initialize(self):
        try:
            versions = await self.engine.start()
            result = await self.engine.call("create", config=self.config.model_dump())
            self.actors = result["actors"]
            settings = self.config.scenario.complexity.beliefs if self.config.scenario.complexity else None
            if self.config.scenario.research:
                settings = SimpleNamespace(enabled=True, **self.config.scenario.research.evidence.model_dump())
            self.memory = {a: PrivateMemory(a, settings, self.config.cognition, self.config.scenario.profile in ("enterprise_cc4", "enterprise_cc4_research")) for a in self.actors}
            self.bus = MessageBus(self.config.communication, self.actors, self.config.team.architecture)
            self.organization = Organization(self.config, self.actors)
            self.meta['organization_version'] = ORGANIZATION_VERSION
            self.relay_evidence = {}
            for a in self.actors:
                if self.config.scenario.research:
                    self.memory[a].coordination = {"claim_ttl": self.config.team.claim_ttl,
                                                   "claim_delivery_ticks": 1 + self.config.communication.extra_delay}
                self.memory[a].observe(result["observations"][a], result["views"][a])
            self.meta.update(status="ready", world_id=result["world"]["world_id"])
            self.structural_diagnostics = structure(self.config, result["truth"])
            qualification = None
            excluded = False
            if self.config.scenario.research:
                qualification = await self.engine.call("qualify", config=self.config.model_dump())
                self.store.write_json(self.directory / "qualification.json", qualification)
                self.meta["feasibility_status"] = qualification["status"]
                excluded = self.config.purpose == "evaluation" and qualification["status"] != "native_witness_validated"
            self.store.write_json(self.directory / "world.json", result.pop("world"))
            self.store.write_json(self.directory / "manifest.json", {"schema_version": self.config.schema_version, "versions": versions, "config_hash": self.meta["config_hash"], "code_fingerprint": self.meta["code_fingerprint"], "prompt_hashes": self.cognition.prompt_hashes, "world_id": self.meta["world_id"], "complexity": self.modules, "baseline": describe_policy(self.config.cognition.scripted_policy), "organization": {"version": ORGANIZATION_VERSION, "assignment_eligibility": "Owned mechanical prerequisites and locally visible original citations; independent of strategy ranking"}, "structural_diagnostics": self.structural_diagnostics, "qualification": qualification or "Software prototype; enterprise research calibration pending"})
            if excluded:
                self.meta.update(status="errored", termination_reason="unverified_world",
                    error="Research world is unverified; excluded from evaluation. See qualification.json")
            self.persist(result)
            if excluded:
                raise ValueError(self.meta["error"])
        except BaseException as exc:
            self.meta.update(status="errored", termination_reason=self.meta.get("termination_reason") or "initialization_error", error=str(exc))
            self.store.update(self.meta)
            await self.engine.close()
            raise
        return self.meta

    def persist(self, result):
        frame = dict(result, complexity=self.modules, status=self.meta["status"], messages=self.bus.snapshot(), communication_topology=self.bus.topology(result["tick"]), private_views={a: self.memory[a].public_view(self.mission(), self.budget()) for a in self.actors}, coordinator={"delivered_reports": copy.deepcopy(self.organization.reports), "assignments": copy.deepcopy(self.organization.assignments)} if self.config.team.architecture == "hierarchy" else None, cognition=self.cognition.summary(), manual_intervention=self.meta["manual_intervention"])
        frame["decisions"] = copy.deepcopy(result.get("decisions", {}))
        frame["diagnostics"] = {"structure": self.structural_diagnostics,
            "behavior": reduce_decisions(self.frames + [frame])}
        self.frames.append(frame)
        self.store.save_frame(self.id, frame)
        self.meta.update(tick=result["tick"], updated_at=now(), metrics=metrics(self.frames, self.cognition.summary(), self.config.schedule.max_ticks, self.meta.get('termination_reason')))
        self.store.update(self.meta)

    def budget(self):
        return {"remaining_team_tokens": max(0, self.config.cognition.max_team_tokens - self.cognition.used)}

    def mission(self):
        result = {"objective": "privileged_access_all", "target_names": self.config.scenario.targets, "architecture": self.config.team.architecture, "worker_count": self.config.team.workers}
        if self.config.scenario.mission:
            result.update(objective="sustained_privileged_access", requirements=self.config.scenario.mission.model_dump())
        # Requirements are public. True team progress and peer access never enter
        # agent/coordinator prompts through this object.
        return result

    async def bridge_messages(self, deliveries):
        for message in deliveries.get("Coordinator", []):
            if message["kind"] == "report" and message["sender"] in self.actors:
                for eid in message["evidence_ids"]:
                    if eid.split(":", 1)[0] == message["sender"]:
                        self.relay_evidence.setdefault(eid, message["resolved_tick"])
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
                    authorized = m["sender"] == origin or (m["sender"] == "Coordinator" and m["kind"] == "assignment" and eid in self.relay_evidence and self.relay_evidence[eid] <= m["created_tick"])
                    if origin in self.memory and self.memory[origin].temporal:
                        authorized = authorized and any(o["evidence_id"] == eid and o.get("received_tick", o["tick"]) <= m["created_tick"] for o in self.memory[origin].observations)
                    if origin in self.actors and authorized:
                        groups.setdefault(origin, []).append(eid)
                    else:
                        self.store.event(self.id, {"type": "intel_rejected", "tick": m["resolved_tick"], "message_id": m["id"], "recipient": actor, "evidence_id": eid, "reason": "Evidence was not observed by this sender or received by the coordinator before relay"})
                for origin, ids in groups.items():
                    if self.config.scenario.research:
                        known = self.memory[actor].accepted_peer_evidence | {o["evidence_id"] for o in self.memory[actor].observations}
                        ids = [eid for eid in ids if eid not in known]
                        if not ids:
                            continue
                    update = await self.engine.call("ingest_intel", sender=origin, recipient=actor, evidence_ids=ids)
                    self.memory[actor].accepted_peer_evidence.update(update["accepted_evidence"])
                    self.memory[actor].accept_intel_view(update)
                    self.memory[actor].report(update["address_fragment"], update["accepted_evidence"], origin, m["resolved_tick"], update.get("evidence"))
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
            if any(self.memory[actor].view.get("pending_action") for actor in overrides):
                raise ValueError("A selected worker is busy; advance until its current action completes")
            if overrides:
                self.meta["manual_intervention"] = True
                self.store.event(self.id, {"type": "manual_intervention", "tick": self.meta["tick"] + 1, "overrides": overrides})
            tick = self.meta["tick"] + 1
            self.organization.decisions = {}
            for memory in self.memory.values():
                memory.advance_clock(tick)
            try:
                deliveries, delivery_events = self.bus.deliver(tick)
                await self.bridge_messages(deliveries)
                if self.config.team.architecture == "hierarchy":
                    coord_view = self.organization.coordinator_view(deliveries.get("Coordinator", []), tick)
                    coord_view["mission"] = self.mission()
                    if self.config.scenario.research:
                        from packages.contracts.research_catalog import PUBLIC_CATALOG
                        coord_view["catalog"] = copy.deepcopy(PUBLIC_CATALOG)
                    defaults = self.organization.scripted_assignments()
                    tasks = await self.cognition.coordinator(coord_view, defaults) if coord_view["delivered_reports"] else {}
                    if self.config.scenario.research:
                        tasks, rejected = self.organization.admit_hierarchy_assignments(tasks,tick)
                        for rejection in rejected:
                            self.store.event(self.id,dict(rejection,type='hierarchy_assignment_suppressed',tick=tick))
                    for actor, task in tasks.items():
                        if actor in self.bus.neighbors("Coordinator"):
                            if self.config.scenario.research:
                                task = dict(task, coordination_reports=self.organization.reported_progress(actor))
                            self.bus.enqueue("Coordinator", [actor], "assignment", task, task["evidence_ids"], tick)
                proposals = {}
                organization_rejections = {}
                for actor in self.actors:
                    memory = self.memory[actor]
                    if memory.view.get("pending_action"):
                        proposals[actor] = {"action": "Sleep", "rationale": "Waiting for the admitted native action to complete"}
                        continue
                    preferred = self.organization.preferred(memory, tick)
                    if actor in overrides:
                        proposals[actor] = overrides[actor]
                    else:
                        view = memory.public_view(self.mission(), self.budget())
                        view["eligible_candidates"] = candidates(memory)
                        proposed = await self.cognition.worker(actor, view, preferred)
                        assigned = self.organization.assigned(memory, tick) if self.config.scenario.research and self.config.team.architecture == 'hierarchy' else preferred
                        if self.config.team.architecture == "hierarchy" and proposed["action"] != "Sleep" and key(proposed) != key(assigned):
                            organization_rejections[actor] = {"proposal": proposed, "rejection": "Hierarchy worker action does not match a locally eligible delivered assignment"}
                            proposals[actor] = {"action": "Sleep", "rationale": "Organization gateway rejected an unassigned action"}
                        else:
                            proposals[actor] = proposed
                suppressed = []
                decisions = copy.deepcopy(self.organization.decisions)
                for actor, trace in decisions.items():
                    trace.update(selected=copy.deepcopy(proposals[actor]), organization=self.config.team.architecture,
                                 manual_override=actor in overrides)
                for actor, proposal in list(proposals.items()):
                    memory = self.memory[actor]
                    if not memory.temporal or proposal["action"] == "Sleep":
                        continue
                    label, target = proposal["action"], proposal.get("target")
                    field = "subnet" if label == "DiscoverRemoteSystems" else "hostname" if label in ("PrivilegeEscalate", "EstablishPivot", "InspectArtifacts") else "ip_address"
                    available = target in memory.view["known"][field]
                    if label in ("ExploitRemoteService", "AttemptAccess"):
                        available = available and target in memory.view["scan_cache"].get(str(proposal.get("session", 0)), {})
                    if label == "AttemptAccess" and proposal.get("method") == "credential_login":
                        available = available and proposal.get("token_ref") in memory.view.get("possessed_tokens", [])
                    if proposal.get("basis_evidence_ids"):
                        visible = {r["evidence_id"] for r in memory.research_evidence} | set(memory.evidence_ids())
                        available = available and set(proposal["basis_evidence_ids"]) <= visible
                    if not available:
                        organization_rejections[actor] = {"proposal": proposal, "rejection": "Target/service evidence has not been delivered to this worker", "preconditions": {"private_evidence_available": False}}
                        proposals[actor] = {"action": "Sleep", "rationale": "Private evidence gateway rejected unavailable information"}
                if self.config.scenario.research and self.config.team.architecture == "swarm":
                    for actor, proposal in list(proposals.items()):
                        if actor not in overrides and not self.memory[actor].view.get("pending_action"):
                            proposals[actor] = self.organization.admit_swarm(self.memory[actor], proposal, tick)
                if self.config.schedule.mode == "team_cap_one":
                    # CC4 caps admission to one in-flight team action. Legacy
                    # actions complete within the tick, preserving prior behavior.
                    busy = any(m.view.get("pending_action") for m in self.memory.values())
                    chosen = -1 if busy else (tick - 1) % len(self.actors)
                    for index, actor in enumerate(self.actors):
                        if index != chosen:
                            suppressed.append({"actor": actor, "proposal": proposals[actor]})
                            proposals[actor] = {"action": "Sleep", "rationale": "Neutral one-action team capacity limit"}
                for actor, trace in decisions.items():
                    trace["admitted_proposal"] = copy.deepcopy(proposals[actor])
                result = await self.engine.call("step", proposals=proposals)
                for record in result["actions"]:
                    if record["actor"] in organization_rejections:
                        record.update(valid=False, preconditions={"delivered_assignment": False})
                        record.update(organization_rejections[record["actor"]])
                    memory = self.memory[record["actor"]]
                    memory.history.append(dict(perceived_action(record) if memory.temporal else record, belief_epoch=memory.epoch, observed_tick=tick))
                for actor in self.actors:
                    memory = self.memory[actor]
                    memory.observe(result["observations"][actor], result["views"][actor], next(record for record in result["actions"] if record["actor"] == actor))
                    if self.config.team.architecture == "hierarchy":
                        report = {"candidates": self.organization.options(memory, tick), "recent_actions": memory.history[-4:], "known": memory.view["known"], "sessions": memory.view["sessions"], "pending_action": memory.view.get("pending_action")}
                        if self.config.scenario.research:
                            report.update(research_evidence=memory.public_view(self.mission(), self.budget())["research_evidence"],
                                          catalog=copy.deepcopy(memory.view["catalog"]),
                                          possessed_tokens=list(memory.view.get("possessed_tokens", [])))
                        if self.config.cognition.scripted_policy != "legacy":
                            report["belief_epoch"] = memory.epoch
                        if memory.temporal:
                            report.update(belief_epoch=memory.epoch, evidence_age_summary={"stale": sum(r["stale"] for r in memory.ledger.snapshot(tick)["records"])})
                        self.bus.enqueue(actor, self.bus.neighbors(actor), "report", report, memory.evidence_ids(), tick)
                    elif self.config.team.architecture == "swarm":
                        actual = next(record["proposal"] for record in result["actions"] if record["actor"] == actor)
                        if self.config.scenario.research:
                            actual = self.organization.claim_intents.get(actor, actual)
                        payload = {"action_key": key(actual), "proposal": actual, "known": memory.view["known"]}
                        if self.config.scenario.research:
                            payload["reported_sessions"] = copy.deepcopy(memory.view["sessions"])
                        self.bus.enqueue(actor, self.bus.neighbors(actor), "claim", payload, memory.evidence_ids(), tick)
                result.update(delivery_events=delivery_events, suppressed_proposals=suppressed, decisions=decisions)
                reason = "mission_success" if result["score"]["mission_success"] else result["score"].get("mission_failure", {}).get("reason") if result["score"].get("mission_failure") else "access_lost" if result["score"].get("all_access_lost") else "native_done" if result["native_done"] else "tick_limit" if tick >= self.config.schedule.max_ticks else None
                if reason:
                    self.meta.update(status="completed", termination_reason=reason)
                elif self.meta["status"] != "running":
                    self.meta["status"] = "paused"
                self.persist(result)
                if reason:
                    await self.engine.close()
                return self.meta
            except BaseException as exc:
                ordinary = isinstance(exc, (BudgetExceeded, ProviderRefusal, InvalidDecision, ContextExceeded))
                reason = 'token_budget' if isinstance(exc,BudgetExceeded) else 'provider_refusal' if isinstance(exc,ProviderRefusal) else 'invalid_decision' if isinstance(exc,InvalidDecision) else 'context_limit' if isinstance(exc,ContextExceeded) else 'cancelled' if isinstance(exc,asyncio.CancelledError) else 'runtime_error'
                self.meta.update(status="completed" if ordinary else "errored", termination_reason=reason,
                                 error=str(exc), error_type=type(exc).__name__, updated_at=now())
                self.meta["metrics"] = metrics(self.frames, self.cognition.summary(), self.config.schedule.max_ticks, self.meta.get("termination_reason"))
                self.store.event(self.id, {"type": "error", "tick": tick, "message": str(exc), "cognition": self.cognition.summary()})
                self.store.update(self.meta)
                await self.engine.close()
                if ordinary:
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
            memory = getattr(self, 'memory', {})
            pending = {a: copy.deepcopy(m.view['pending_action']) for a,m in memory.items() if m.view.get('pending_action')}
            if pending and not (self.directory/'interrupted-actions.json').exists():
                self.store.write_json(self.directory/'interrupted-actions.json', {'version':'1.0','tick':self.meta['tick'],
                    'reason':self.meta.get('termination_reason'),'actions':pending,
                    'access_resources':{a:copy.deepcopy(m.view.get('access_resources')) for a,m in memory.items()},
                    'interpretation':'Reserved unfinished actions have unknown outcomes; no completed effect is claimed.'})
                self.store.event(self.id, {'type':'actions_interrupted','tick':self.meta['tick'],'actors':sorted(pending)})
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
