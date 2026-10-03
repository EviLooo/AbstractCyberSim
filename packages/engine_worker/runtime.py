"""The only native-engine adapter. Agent data and privileged truth are separate."""
import copy
import hashlib
import inspect
import json
import random
from ipaddress import IPv4Address, IPv4Network

from CybORG import CybORG
from CybORG.Simulator.Actions import DiscoverRemoteSystems, DiscoverNetworkServices, ExploitRemoteService, PrivilegeEscalate, Sleep
from CybORG.Simulator.Actions.ConcreteActions.Portscan import Portscan
from CybORG.Simulator.SimulationController import SimulationController
from packages.engine_worker.scenario import EnterpriseScenario

CATALOG = {c.__name__: c for c in [Sleep, DiscoverRemoteSystems, DiscoverNetworkServices, ExploitRemoteService, PrivilegeEscalate]}


class RecordingSimulationController(SimulationController):
    """Instrument executions without changing native action ordering/effects."""
    def step(self, actions=None, skip_valid_action_check=False):
        self.execution_trace = []
        return super().step(actions, skip_valid_action_check)

    def execute_action(self, action):
        matching = [name for name, submitted in self.action.items() if submitted is action]
        actor = matching[0] if matching else getattr(action, "agent", None)
        self.execution_trace.append({"actor": actor, "action": str(action), "phase": "joint" if matching else "end_turn"})
        return super().execute_action(action)


class RecordedCybORG(CybORG):
    def _create_env_controller(self, env_config, agents):
        if self.env == "sim":
            return RecordingSimulationController(self.scenario_generator, agents, self.np_random)
        return super()._create_env_controller(env_config, agents)


def normalized(value):
    if isinstance(value, dict):
        return {str(k): normalized(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [normalized(x) for x in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if hasattr(value, "name"):
        return value.name
    if hasattr(value, "tolist"):
        return normalized(value.tolist())
    return str(value)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


class EngineRuntime:
    def __init__(self):
        self.env = None
        self.evidence = {}

    def create(self, config):
        if "state.sessions['Red']" in inspect.getsource(Portscan.execute):
            raise ValueError("Engine source patch missing. Run python tools/patch_engine.py")
        self.config = config
        self.tick = 0
        self.evidence = {}
        self.scheduler = random.Random(config["schedule"]["seed"])
        self.env = RecordedCybORG(EnterpriseScenario(config), "sim", seed=config["scenario"]["world_seed"])
        self.env.reset(seed=config["scenario"]["world_seed"])
        self.actors = ["Red_{}".format(i) for i in range(config["team"]["workers"])]
        observations = {a: self.record(a, self.env.get_observation(a)) for a in self.actors}
        snapshot = self.snapshot()
        # Include all technical initial information in the fingerprint; omit
        # organizational configuration so both modes share the same world ID.
        initial = {"snapshot": snapshot, "native_truth": self.native_truth(), "profile": config["scenario"]["profile"], "engine": "2742b5e0ce4330c9b14006b38acd3b5ebe00d6fd", "targets": config["scenario"]["targets"], "defender": config["scenario"]["defender"]}
        self.world_id = hashlib.sha256(canonical(initial).encode()).hexdigest()
        return {"tick": 0, "actors": self.actors, "observations": observations, "views": self.views(), "truth": snapshot, "world": dict(initial, world_id=self.world_id), "score": self.score(), "actions": []}

    def record(self, actor, observation):
        raw = copy.deepcopy(observation)
        eid = "{}:{}:{}".format(actor, self.tick, len(self.evidence))
        self.evidence[eid] = {"actor": actor, "raw": raw}
        return {"evidence_id": eid, "actor": actor, "tick": self.tick, "data": normalized(raw)}

    def native_truth(self):
        fields = ["Processes", "Interfaces", "Sessions", "Files", "User info", "System info", "Services"]
        info = {name: {f: "All" for f in fields} for name in self.env.environment_controller.state.hosts}
        return normalized(self.env.environment_controller.state.get_true_state(info).data)

    def snapshot(self):
        state = self.env.environment_controller.state
        subnets = [{"id": name, "cidr": str(cidr)} for name, cidr in state.subnet_name_to_cidr.items()]
        cidr_names = {str(s["cidr"]): s["id"] for s in subnets}
        hosts = []
        for name, host in state.hosts.items():
            interfaces = [dict(normalized(i.get_state()), **{"IP Address": str(i.ip_address), "Subnet": str(i.subnet), "Interface Name": i.name}) for i in host.interfaces]
            subnet = next((cidr_names.get(str(i.subnet)) for i in host.interfaces if str(i.ip_address) != "127.0.0.1"), None)
            sessions = []
            for actor, actor_sessions in state.sessions.items():
                for session in actor_sessions.values():
                    if session.hostname == name and session.active:
                        sessions.append(dict(normalized(session.get_state()), privileged=session.username in ["root", "SYSTEM"], id=session.ident))
            hosts.append({"id": name, "subnet": subnet, "router": name.endswith("_router"), "target": name in self.config["scenario"]["targets"], "interfaces": interfaces, "system": normalized(host.get_state()), "services": normalized(host.services), "sessions": sessions})
        edges = [{"id": "--".join(sorted([a, b])), "source": a, "target": b} for a, b in state.link_diagram.edges()]
        return {"hosts": hosts, "edges": sorted(edges, key=lambda e: e["id"]), "subnets": subnets}

    def score(self):
        state = self.env.environment_controller.state
        controlled = set()
        privileged = set()
        for actor in self.actors:
            for s in state.sessions[actor].values():
                if s.active:
                    controlled.add(s.hostname)
                    if s.username in ("root", "SYSTEM"):
                        privileged.add(s.hostname)
        targets = set(self.config["scenario"]["targets"])
        return {"controlled_hosts": sorted(controlled), "privileged_hosts": sorted(privileged), "target_count": len(targets), "targets_reached": len(targets & privileged), "mission_success": targets <= privileged}

    def views(self):
        state = self.env.environment_controller.state
        result = {}
        for actor in self.actors:
            space = self.env.get_action_space(actor)
            known = {field: [str(k) for k, flag in space.get(field, {}).items() if flag] for field in ["ip_address", "subnet", "hostname"]}
            sessions = [{"id": s.ident, "hostname": s.hostname, "username": s.username, "privileged": s.username in ("root", "SYSTEM"), "controller": hasattr(s, "ports"), "active": s.active} for s in state.sessions[actor].values()]
            controllers = [s for s in state.sessions[actor].values() if s.active and hasattr(s, "ports")]
            # This is the actor's own native scan cache. No peer cache or hidden
            # address inventory is exposed, even when keys exist with known=False.
            caches = {str(s.ident): {str(ip): list(ports) for ip, ports in s.ports.items()} for s in controllers}
            result[actor] = {"actor": actor, "known": known, "sessions": sessions, "scan_cache": caches}
        return result

    def ingest_intel(self, sender, recipient, evidence_ids):
        if sender not in self.actors or recipient not in self.actors:
            raise ValueError("Intel bridge only accepts same-team native actors")
        fragment = {}
        accepted = []
        for eid in evidence_ids:
            evidence = self.evidence.get(eid)
            if not evidence or evidence["actor"] != sender:
                continue
            for hostid, data in evidence["raw"].items():
                if not isinstance(data, dict):
                    continue
                interfaces = []
                for interface in data.get("Interface", []):
                    safe = {k: copy.deepcopy(v) for k, v in interface.items() if k in ["IP Address", "Subnet"]}
                    if safe:
                        interfaces.append(safe)
                if interfaces:
                    fragment.setdefault(hostid, {})["Interface"] = interfaces
                hostname = data.get("System info", {}).get("Hostname")
                if hostname:
                    fragment.setdefault(hostid, {})["System info"] = {"Hostname": hostname}
            accepted.append(eid)
        if fragment:
            self.env.environment_controller.agent_interfaces[recipient].update(fragment)
        return {"accepted_evidence": accepted, "address_fragment": normalized(fragment), "view": self.views()[recipient]}

    def construct(self, actor, proposal):
        action = proposal.get("action", "Sleep")
        if action not in CATALOG:
            raise ValueError("Unsupported action")
        if action == "Sleep":
            return Sleep()
        session = proposal.get("session", 0)
        own = self.env.environment_controller.state.sessions[actor].get(session)
        if own is None or not own.active or not hasattr(own, "ports"):
            raise ValueError("Action requires an active, actor-owned controlling session")
        target = proposal.get("target")
        view = self.views()[actor]
        kwargs = {"session": session, "agent": actor}
        if action == "DiscoverRemoteSystems":
            if target not in view["known"]["subnet"]:
                raise ValueError("Subnet has not been observed")
            kwargs["subnet"] = IPv4Network(target)
        elif action == "PrivilegeEscalate":
            if target not in view["known"]["hostname"] or not any(s["hostname"] == target and s["active"] for s in view["sessions"]):
                raise ValueError("Escalation requires a known host with an active owned session")
            kwargs["hostname"] = target
        else:
            if target not in view["known"]["ip_address"]:
                raise ValueError("Address has not been observed")
            kwargs["ip_address"] = IPv4Address(target)
            if action == "ExploitRemoteService" and IPv4Address(target) not in own.ports:
                raise ValueError("Exploit requires this actor's own service scan")
        native = CATALOG[action](**kwargs)
        checked = self.env.environment_controller.replace_action_if_invalid(native, self.env.environment_controller.agent_interfaces[actor])
        if type(checked).__name__ == "InvalidAction":
            raise ValueError("Native action-space validation rejected the action")
        return native

    def preconditions(self, view, proposal):
        action = proposal.get("action", "Sleep")
        if action == "Sleep":
            return {}
        session = proposal.get("session", 0)
        controller = next((s for s in view["sessions"] if s["id"] == session), None)
        target = proposal.get("target")
        field = "subnet" if action == "DiscoverRemoteSystems" else "hostname" if action == "PrivilegeEscalate" else "ip_address"
        result = {"active_owned_controller": bool(controller and controller["active"] and controller["controller"]), "observed_target": target in view["known"][field]}
        if action == "ExploitRemoteService":
            result["own_service_scan"] = target in view["scan_cache"].get(str(session), {})
        if action == "PrivilegeEscalate":
            result["active_owned_target_session"] = any(s["hostname"] == target and s["active"] for s in view["sessions"])
        return result

    def state_delta(self, before, after):
        previous = {s["id"]: s for s in before["sessions"]}
        current = {s["id"]: s for s in after["sessions"]}
        return {"sessions_added": [s for sid, s in current.items() if sid not in previous], "sessions_lost": [s for sid, s in previous.items() if s["active"] and (sid not in current or not current[sid]["active"])], "privilege_changes": [{"session_id": sid, "hostname": s["hostname"], "before": previous[sid]["username"], "after": s["username"]} for sid, s in current.items() if sid in previous and s["username"] != previous[sid]["username"]], "knowledge_added": {field: sorted(set(after["known"][field]) - set(before["known"][field])) for field in before["known"]}, "scan_cache_updates": {sid: {ip: ports for ip, ports in cache.items() if before["scan_cache"].get(sid, {}).get(ip) != ports} for sid, cache in after["scan_cache"].items() if cache != before["scan_cache"].get(sid, {})}}

    def step(self, proposals):
        if set(proposals) - set(self.actors):
            raise ValueError("Unknown actor binding")
        actions, records = {}, {}
        before = self.views()
        order = self.actors[:]
        self.scheduler.shuffle(order)
        for actor in order:
            proposal = proposals.get(actor, {"action": "Sleep"})
            record = {"actor": actor, "proposal": proposal, "valid": True, "rejection": None, "preconditions": self.preconditions(before[actor], proposal)}
            try:
                actions[actor] = self.construct(actor, proposal)
            except (ValueError, TypeError, KeyError) as exc:
                actions[actor] = Sleep()
                record.update(valid=False, rejection=str(exc))
            record["native_action"] = str(actions[actor])
            records[actor] = record
        observations, _, dones, _ = self.env.parallel_step(actions=dict(actions))
        self.tick += 1
        after = self.views()
        normalized_obs = {}
        for actor in self.actors:
            normalized_obs[actor] = self.record(actor, observations.get(actor, {}))
            records[actor]["outcome"] = normalized_obs[actor]["data"].get("success", "UNKNOWN")
            records[actor]["state_delta"] = self.state_delta(before[actor], after[actor])
        trace = self.env.environment_controller.execution_trace
        execution = [item["actor"] for item in trace if item["phase"] == "joint"]
        for actor in self.actors:
            native = self.env.environment_controller.action.get(actor)
            if native is not None:
                records[actor]["native_action"] = str(native)
                concrete = getattr(native, "sub_action", None)
                records[actor]["concrete_action"] = str(concrete) if concrete else None
        return {"tick": self.tick, "native_step_count": self.env.environment_controller.step_count, "observations": normalized_obs, "views": after, "truth": self.snapshot(), "score": self.score(), "actions": list(records.values()), "submission_order": order, "execution_order": execution, "execution_trace": trace, "native_done": any(dones.get(a, False) for a in self.actors)}
