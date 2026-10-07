"""CC4 adapter: native actors stay behind a logical worker/evidence boundary."""
import copy
import hashlib
import random
from ipaddress import IPv4Address, IPv4Network

from CybORG import CybORG
from CybORG.Simulator.SimulationController import SimulationController
from CybORG.Simulator.Actions import (
    Sleep, DiscoverRemoteSystems, AggressiveServiceDiscovery,
    ExploitRemoteService, PrivilegeEscalate, Restore, Monitor,
)
from packages.engine_worker.common import canonical, normalized
from packages.engine_worker.cc4.scenario import ResearchScenario
from packages.engine_worker.cc4.defender import RestorePolicy
from packages.engine_worker.cc4.routes import settings, install_blocks, EstablishPivot
from packages.engine_worker.cc4.route_pressure import RoutePressure
from CybORG.Simulator.Actions.Action import RemoteAction
from packages.engine_worker.missions import MissionTracker

COMMIT = "8c3c50ca54b176c2de199847944e8dcc035497e3"
CATALOG = {"Sleep": Sleep, "DiscoverRemoteSystems": DiscoverRemoteSystems,
           "DiscoverNetworkServices": AggressiveServiceDiscovery,
           "ExploitRemoteService": ExploitRemoteService, "PrivilegeEscalate": PrivilegeEscalate,
           "EstablishPivot": EstablishPivot}


class RecordingController(SimulationController):
    def step(self, actions=None, skip_valid_action_check=False):
        self.execution_trace = []
        self.monitor_observations = {}
        self.route_traffic = []
        return super().step(actions, skip_valid_action_check)

    def execute_action(self, action):
        actor = getattr(action, "agent", None)
        joint = any(action is item for items in self.action.values() for item in items)
        # Record reachable traffic, not compromise state, for the separate route
        # sensor. Rejected/busy actions and blocked attempts create no such event.
        if joint and (isinstance(action, (AggressiveServiceDiscovery, ExploitRemoteService)) or getattr(action, "research_traffic", False)):
            source = self.state.sessions.get(actor, {}).get(action.session)
            target = self.state.ip_addresses.get(action.ip_address)
            if source and source.active and target and not action.dropped and not action.blocked:
                if not RemoteAction.blocking_host(self.state, source.hostname, target):
                    if RemoteAction.get_route(self.state, target, source.hostname) is not None:
                        self.route_traffic.append({"actor": actor, "source": source.hostname,
                                                   "target": target, "action": action.name})
        result = super().execute_action(action)
        if isinstance(action, Monitor) and not joint:
            # Only this sensor result feeds the defender. Initial inventory or
            # repeatedly combined observations are not fresh security alerts.
            self.monitor_observations[actor] = copy.deepcopy(self._filter_obs(result.copy(), actor).data)
        self.execution_trace.append({"actor": actor, "action": str(action),
            "phase": "joint" if joint else "end_turn", "outcome": normalized(result.data.get("success")),
            "concrete_action": str(action.sub_action) if getattr(action, "sub_action", None) else None})
        return result


class RecordedCybORG(CybORG):
    def __init__(self, generator, seed):
        super().__init__(generator, seed=seed)
        # CC4 has no controller factory hook. Use its normal constructor with a
        # recording subclass; reset(seed) below materializes the selected world.
        self.environment_controller = RecordingController(generator, None, self.np_random)


class EngineRuntime:
    PROFILE = "enterprise_cc4"
    SCENARIO = ResearchScenario
    def __init__(self):
        self.env = None

    def create(self, config):
        if config["scenario"]["profile"] != self.PROFILE:
            raise ValueError("CC4 worker requires its own profile")
        self.config = config
        self.tick = 0
        self.evidence = {}
        self.pending = {}
        self.mission_tracker = MissionTracker(config["scenario"]["targets"], config["scenario"].get("mission"))
        self.scheduler = random.Random(config["schedule"]["seed"])
        self.actors = ["Red_{}".format(i) for i in range(config["team"]["workers"])]
        self.bindings = {actor: "red_agent_{}".format(i) for i, actor in enumerate(self.actors)}
        self.reverse = {native: actor for actor, native in self.bindings.items()}
        self.env = RecordedCybORG(self.SCENARIO(config), config["scenario"]["world_seed"])
        self.env.reset(seed=config["scenario"]["world_seed"])
        self.route_manifest = self.controller.scenario_generator.route_manifest
        install_blocks(self.controller.state, self.route_manifest)
        self.route_pressure = RoutePressure(self.route_manifest, config["scenario"]["world_seed"])
        self.defenders = {name: RestorePolicy(config["scenario"]["cc4"])
                          for name in self.controller.agent_interfaces if name.startswith("blue_")}
        self.initialize_profile()
        observations = {a: self.record(a, self.env.get_observation(self.bindings[a])) for a in self.actors}
        snapshot = self.snapshot()
        initial = {"snapshot": snapshot, "profile": config["scenario"]["profile"],
            "engine": COMMIT, "targets": config["scenario"]["targets"],
            "defender": config["scenario"]["defender"], "cc4": config["scenario"]["cc4"],
            "native_truth": self.native_truth(), "assumptions": {
                "foothold": "equal contractor user-host sessions", "mobile_workers": True,
                "green_activity": "disabled", "automatic_respawn": "disabled",
                "policy_is_not_firewall_enforcement": True}}
        self.world_id = hashlib.sha256(canonical(initial).encode()).hexdigest()
        return {"tick": 0, "native_step_count": 0, "actors": self.actors,
            "observations": observations, "views": self.views(), "truth": snapshot,
            "world": dict(initial, world_id=self.world_id), "score": self.score(),
            "actions": [], "defender_events": [], "engine_profile": self.PROFILE}

    def initialize_profile(self):
        """Profile extension after native reset, before any public observation."""

    def before_joint_step(self, actions):
        return []

    @property
    def controller(self):
        return self.env.environment_controller

    def sessions(self, actor):
        return self.controller.state.sessions[self.bindings[actor]]

    def observation(self, raw):
        """Normalize CC4's field names to the workbench's existing evidence API."""
        data = normalized(copy.deepcopy(raw))
        for host in data.values():
            if not isinstance(host, dict):
                continue
            for interface in host.get("Interface", []):
                if "ip_address" in interface:
                    interface["IP Address"] = interface.pop("ip_address")
            for session in host.get("Sessions", []):
                if session.get("agent") in self.reverse:
                    session["agent"] = self.reverse[session["agent"]]
        return data

    def record(self, actor, raw):
        eid = "{}:{}:{}".format(actor, self.tick, len(self.evidence))
        self.evidence[eid] = {"actor": actor, "raw": copy.deepcopy(raw)}
        return {"evidence_id": eid, "actor": actor, "tick": self.tick, "data": self.observation(raw)}

    def native_truth(self):
        info = {name: {field: "All" for field in ["Processes", "Interfaces", "Sessions", "Files", "User info", "System info", "Services"]}
                for name in self.controller.state.hosts}
        return self.observation(self.controller.state.get_true_state(info).data)

    def snapshot(self):
        state = self.controller.state
        hosts = []
        for name, host in state.hosts.items():
            sessions = [{"id": session.ident, "agent": self.reverse.get(owner, owner),
                "username": session.username, "privileged": session.username in ("root", "SYSTEM"),
                "session_type": normalized(session.session_type)}
                for owner, owned in state.sessions.items() for session in owned.values()
                if session.hostname == name and session.active]
            interfaces = [{"IP Address": str(i.ip_address), "Subnet": str(i.subnet),
                           "Interface Name": i.name} for i in host.interfaces]
            hosts.append({"id": name, "subnet": state.hostname_subnet_map[name].value,
                "router": "_router" in name or name == "internet_root_host", "target": name in self.config["scenario"]["targets"],
                "interfaces": interfaces, "system": normalized(host.get_state()),
                "services": {normalized(key): normalized(service.get_state()) for key, service in host.services.items()}, "sessions": sessions})
        edges = [{"id": "--".join(sorted([a, b])), "source": a, "target": b} for a, b in state.link_diagram.edges()]
        return {"hosts": hosts, "edges": sorted(edges, key=lambda e: e["id"]),
            "subnets": [{"id": name.value if hasattr(name, "value") else str(name), "cidr": str(cidr)}
                        for name, cidr in state.subnet_name_to_cidr.items()],
            "blocks": normalized(state.blocks), "route_manifest": self.route_manifest,
            "route_pressure": self.route_pressure.snapshot(), "mission_phase": state.mission_phase,
            "intended_policy": normalized(state.scenario.allowed_subnets_per_mphase[state.mission_phase])}

    def score(self):
        controlled, privileged = set(), set()
        for actor in self.actors:
            for session in self.sessions(actor).values():
                if session.active:
                    controlled.add(session.hostname)
                    if session.username in ("root", "SYSTEM"):
                        privileged.add(session.hostname)
        targets = set(self.config["scenario"]["targets"])
        mission = self.mission_tracker.update(self.tick, privileged)
        return {"controlled_hosts": sorted(controlled), "privileged_hosts": sorted(privileged),
            "target_count": len(targets), "targets_reached": len(targets & privileged),
            "mission_success": mission["success"], "mission": mission,
            "mission_failure": mission["failure"], "all_access_lost": not controlled}

    def views(self):
        result = {}
        for actor in self.actors:
            space = self.env.get_action_space(self.bindings[actor])
            own = self.sessions(actor)
            pending = self.controller.actions_in_progress.get(self.bindings[actor])
            result[actor] = {"actor": actor,
                "pivot_enabled": settings(self.config)["enabled"],
                "known": {field: [str(k) for k, known in space.get(field, {}).items() if known]
                          for field in ["ip_address", "subnet", "hostname"]},
                "sessions": [{"id": s.ident, "hostname": s.hostname, "username": s.username,
                    "privileged": s.username in ("root", "SYSTEM"), "controller": hasattr(s, "ports"), "active": s.active}
                    for s in own.values()],
                "scan_cache": {str(s.ident): {str(ip): list(ports) for ip, ports in s.ports.items()}
                               for s in own.values() if s.active and hasattr(s, "ports")},
                "pending_action": dict(self.pending[actor], remaining_ticks=pending["remaining_ticks"]) if pending and actor in self.pending else None}
        return result

    def ingest_intel(self, sender, recipient, evidence_ids):
        if sender not in self.actors or recipient not in self.actors:
            raise ValueError("Intel requires same-team workers")
        fragment, accepted, records = {}, [], []
        for eid in evidence_ids:
            evidence = self.evidence.get(eid)
            if not evidence or evidence["actor"] != sender:
                continue
            piece = {}
            for hostid, data in evidence["raw"].items():
                if not isinstance(data, dict):
                    continue
                interfaces = [{k: copy.deepcopy(v) for k, v in item.items() if k in ["ip_address", "Subnet"]}
                              for item in data.get("Interface", [])]
                if any(interfaces):
                    fragment.setdefault(hostid, {})["Interface"] = [i for i in interfaces if i]
                    piece.setdefault(hostid, {})["Interface"] = [i for i in interfaces if i]
                hostname = data.get("System info", {}).get("Hostname")
                if hostname:
                    fragment.setdefault(hostid, {})["System info"] = {"Hostname": hostname}
                    piece.setdefault(hostid, {})["System info"] = {"Hostname": hostname}
                # Service assessments can be forwarded as verified evidence,
                # but never populate the recipient's native source scan cache.
                if data.get("Route clue"):
                    piece.setdefault(hostid, {})["Route clue"] = copy.deepcopy(data["Route clue"])
            accepted.append(eid)
            records.append({"evidence_id": eid, "tick": int(eid.split(":")[1]), "actor": sender, "data": self.observation(piece)})
        if fragment:
            self.controller.agent_interfaces[self.bindings[recipient]].update(fragment)
        public_fragment = copy.deepcopy(fragment)
        for record in records:
            for hostid, data in record["data"].items():
                if isinstance(data, dict) and data.get("Route clue"):
                    public_fragment.setdefault(hostid, {})["Route clue"] = copy.deepcopy(data["Route clue"])
        return {"accepted_evidence": accepted, "address_fragment": self.observation(public_fragment), "evidence": records, "view": self.views()[recipient]}

    def construct(self, actor, proposal):
        label = proposal.get("action", "Sleep")
        if label not in CATALOG:
            raise ValueError("Unsupported action")
        if label == "Sleep":
            return Sleep()
        sid = proposal.get("session", 0)
        own = self.sessions(actor).get(sid)
        if not own or not own.active or not hasattr(own, "ports"):
            raise ValueError("Action requires an active actor-owned controller")
        view = self.views()[actor]
        target = proposal.get("target")
        field = "subnet" if label == "DiscoverRemoteSystems" else "hostname" if label in ("PrivilegeEscalate", "EstablishPivot") else "ip_address"
        if target not in view["known"][field]:
            raise ValueError("Target has not been observed")
        kwargs = {"session": sid, "agent": self.bindings[actor]}
        if label == "DiscoverRemoteSystems":
            kwargs["subnet"] = IPv4Network(target)
        elif label in ("PrivilegeEscalate", "EstablishPivot"):
            if not any(s.active and s.hostname == target for s in self.sessions(actor).values()):
                raise ValueError("Escalation requires active owned target access")
            kwargs["hostname"] = target
            if label == "EstablishPivot":
                if not settings(self.config)["enabled"]:
                    raise ValueError("Pivot deployment requires enabled routes")
                if not any(s.active and s.hostname == target and s.has_privileged_access() and not s.is_escalate_sandbox and not hasattr(s, "ports") for s in self.sessions(actor).values()):
                    raise ValueError("Pivot requires an active privileged actor-owned shell")
        else:
            kwargs["ip_address"] = IPv4Address(target)
            if label == "ExploitRemoteService" and IPv4Address(target) not in own.ports:
                raise ValueError("Exploit requires this worker's own service scan")
        action = CATALOG[label](**kwargs)
        if label == "ExploitRemoteService":
            duration = self.route_pressure.duration(self.controller.state.ip_addresses.get(IPv4Address(target)))
            if duration is not None:
                # Uses CC4's native busy/continuation clock; no parallel timer.
                action.duration = duration
        checked = self.controller.replace_action_if_invalid(action, self.controller.agent_interfaces[self.bindings[actor]])
        if type(checked).__name__ == "InvalidAction":
            raise ValueError("Native action-space validation rejected the action")
        return action

    def preconditions(self, view, proposal):
        label = proposal.get("action", "Sleep")
        if label == "Sleep":
            return {}
        sid = proposal.get("session", 0)
        session = next((s for s in view["sessions"] if s["id"] == sid), None)
        field = "subnet" if label == "DiscoverRemoteSystems" else "hostname" if label in ("PrivilegeEscalate", "EstablishPivot") else "ip_address"
        checks = {"active_owned_controller": bool(session and session["active"] and session["controller"]),
                  "observed_target": proposal.get("target") in view["known"][field]}
        if label == "ExploitRemoteService":
            checks["own_service_scan"] = proposal.get("target") in view["scan_cache"].get(str(sid), {})
        return checks

    def state_delta(self, before, after):
        old = {s["id"]: s for s in before["sessions"]}
        new = {s["id"]: s for s in after["sessions"]}
        return {"sessions_added": [s for sid, s in new.items() if sid not in old or old[sid]["hostname"] != s["hostname"]],
            "controller_changes": [{"session_id": sid, "hostname": s["hostname"], "controller": s["controller"]}
                                   for sid, s in new.items() if sid in old and s["controller"] != old[sid]["controller"]],
            "sessions_lost": [s for sid, s in old.items() if s["active"] and (sid not in new or not new[sid]["active"] or new[sid]["hostname"] != s["hostname"])],
            "privilege_changes": [{"session_id": sid, "hostname": s["hostname"], "before": old[sid]["username"], "after": s["username"]}
                                  for sid, s in new.items() if sid in old and s["hostname"] == old[sid]["hostname"] and s["username"] != old[sid]["username"]],
            "knowledge_added": {field: sorted(set(after["known"][field]) - set(before["known"][field])) for field in before["known"]},
            "scan_cache_updates": {sid: {ip: ports for ip, ports in cache.items() if before["scan_cache"].get(sid, {}).get(ip) != ports}
                                   for sid, cache in after["scan_cache"].items() if cache != before["scan_cache"].get(sid, {})}}

    def step(self, proposals):
        if set(proposals) - set(self.actors):
            raise ValueError("Unknown actor binding")
        before = self.views()
        order = self.actors[:]
        self.scheduler.shuffle(order)
        actions, records = {}, {}
        for actor in order:
            proposal = proposals.get(actor, {"action": "Sleep"})
            prior = before[actor]["pending_action"]
            if prior:
                records[actor] = {"actor": actor, "proposal": prior["proposal"], "valid": True,
                    "rejection": None, "submitted": False, "started_tick": prior["started_tick"],
                    "duration": prior["duration"], "native_action": prior["native_action"],
                    "preconditions": {}, "lifecycle": "continuing"}
                if proposal.get("action", "Sleep") != "Sleep":
                    records[actor].update(rejected_proposal=proposal, rejection="Worker is busy; new action not admitted")
                continue
            record = {"actor": actor, "proposal": proposal, "valid": True, "rejection": None,
                "submitted": proposal.get("action", "Sleep") != "Sleep", "started_tick": self.tick + 1,
                "preconditions": self.preconditions(before[actor], proposal), "lifecycle": "submitted"}
            try:
                native = self.construct(actor, proposal)
            except (ValueError, TypeError, KeyError) as error:
                native = Sleep()
                record.update(valid=False, rejection=str(error), lifecycle="rejected")
            actions[self.bindings[actor]] = native
            record.update(native_action=str(native), duration=native.duration)
            records[actor] = record
            if record["valid"] and proposal.get("action", "Sleep") != "Sleep":
                self.pending[actor] = {key: copy.deepcopy(record[key]) for key in ["proposal", "started_tick", "duration", "native_action"]}

        defender_events = self.route_pressure.transition(self.tick + 1)
        self.route_pressure.apply_blocks(self.controller.state)
        if self.config["scenario"]["defender"] == "reactive_restore":
            for name, policy in self.defenders.items():
                obs = getattr(self.controller, "monitor_observations", {}).get(name, {})
                defender_events.extend(dict(event, actor=name) for event in policy.observe(obs, self.tick))
                if not self.controller.actions_in_progress.get(name):
                    space = self.env.get_action_space(name)
                    decision = policy.choose(self.tick, {host for host, known in space["hostname"].items() if known})
                    if decision:
                        actions[name] = Restore(session=0, agent=name, hostname=decision["host"])
                        defender_events.append(dict(decision, actor=name, type="defender_response_started", action="Restore", duration=5))

        defender_events.extend(self.before_joint_step(actions))
        observations, _, dones, _ = self.env.parallel_step(actions=actions)
        self.tick += 1
        defender_events.extend(self.route_pressure.observe(self.controller.route_traffic, self.tick))
        after = self.views()
        trace = copy.deepcopy(self.controller.execution_trace)
        for item in trace:
            item["actor"] = self.reverse.get(item["actor"], item["actor"])
            if item["actor"] and item["actor"].startswith("blue_") and item["action"].startswith("Restore ") and item["phase"] == "joint":
                defender_events.append({"type": "defender_response_completed", "actor": item["actor"],
                    "host": item["action"][len("Restore "):], "effect_tick": self.tick,
                    "outcome": item["outcome"]})
            if item["actor"] in self.actors:
                for native, public in self.reverse.items():
                    item["action"] = item["action"].replace(native, public)
        # Disclose the limited template clue only when this actor actually
        # completes a successful service scan. It goes through ordinary delayed
        # evidence/private memory and verified message delivery.
        for actor, record in records.items():
            executed = next((item for item in trace if item["actor"] == actor and item["phase"] == "joint"), None)
            if record["valid"] and record["proposal"].get("action") == "DiscoverNetworkServices" and executed and executed["outcome"] == "TRUE":
                ip = record["proposal"]["target"]
                host = self.controller.state.ip_addresses.get(IPv4Address(ip))
                assessment = self.route_pressure.assessment(host)
                if assessment:
                    raw = observations.setdefault(self.bindings[actor], {})
                    raw.setdefault(str(ip), {})["Route clue"] = assessment
        deltas = {actor: self.record(actor, observations.get(self.bindings[actor], {})) for actor in self.actors}
        for actor, record in records.items():
            pending = self.controller.actions_in_progress.get(self.bindings[actor])
            executed = next((item for item in trace if item["actor"] == actor and item["phase"] == "joint"), None)
            record["remaining_ticks"] = pending["remaining_ticks"] if pending else 0
            record["outcome"] = "IN_PROGRESS" if pending else executed["outcome"] if executed else "UNKNOWN"
            record["concrete_action"] = executed["concrete_action"] if executed else None
            if record["valid"] and record["proposal"].get("action", "Sleep") != "Sleep" and not pending:
                record["lifecycle"] = "completed"
            record["state_delta"] = self.state_delta(before[actor], after[actor])
            if not pending:
                self.pending.pop(actor, None)
        return {"tick": self.tick, "native_step_count": self.controller.step_count,
            "observations": deltas, "views": after, "truth": self.snapshot(), "score": self.score(),
            "actions": list(records.values()), "submission_order": order,
            "execution_order": [item["actor"] for item in trace if item["phase"] == "joint"],
            "execution_trace": trace, "defender_events": defender_events,
            "engine_profile": self.PROFILE, "native_done": any(dones.values())}
