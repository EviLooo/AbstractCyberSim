"""Research profile uses the shared native joint clock and private worker views."""
import copy
from ipaddress import IPv4Address

from packages.engine_worker.cc4.runtime import EngineRuntime as CC4Runtime
from packages.engine_worker.cc4.research.compiler import InvestigationScenario
from packages.engine_worker.cc4.research.state import ResearchState
from packages.engine_worker.cc4.research.actions import Probe, InspectArtifacts, AttemptAccess
from packages.contracts.research_catalog import PUBLIC_CATALOG
from packages.engine_worker.cc4.research.evidence import disclosed_fields, token_refs
from packages.engine_worker.cc4.research.changes import SharedResponse


class EngineRuntime(CC4Runtime):
    PROFILE = "enterprise_cc4_research"
    SCENARIO = InvestigationScenario

    def initialize_profile(self):
        manifest = self.controller.scenario_generator.research_manifest
        self.research = ResearchState(manifest, self.bindings.values())
        self.controller.state.research = self.research
        self.response = SharedResponse(manifest["change"], self.config["scenario"]["targets"])

    def before_joint_step(self, actions):
        # Selection consumes only traffic from the previous completed native
        # tick and Blue-owned coverage, not attacker session/mission truth.
        coverage = {s.hostname for name in self.controller.agent_interfaces if name.startswith("blue_")
                    for s in self.controller.state.sessions[name].values() if s.active}
        events = self.response.observe(getattr(self.controller, "route_traffic", []), self.tick, coverage)
        chosen = self.response.choose(self.tick + 1, self.controller)
        if chosen:
            name, native, event = chosen
            actions[name] = native
            events.append(event)
        return events

    def snapshot(self):
        result = super().snapshot()
        if hasattr(self, "research"):
            result["research_truth"] = copy.deepcopy(self.research.manifest)
            result["research_truth"]["attempts"] = copy.deepcopy(self.research.attempts)
            result["research_truth"]["response"] = self.response.snapshot()
        return result

    def views(self):
        result = super().views()
        for actor, view in result.items():
            view["pivot_enabled"] = True
            view["catalog"] = copy.deepcopy(PUBLIC_CATALOG)
            view["possessed_tokens"] = sorted(self.research.possession[self.bindings[actor]])
            view["access_resources"] = self.research.public_resources()
        return result

    def ingest_intel(self, sender, recipient, evidence_ids):
        result = super().ingest_intel(sender, recipient, evidence_ids)
        for record in result["evidence"]:
            fields = disclosed_fields(self.evidence[record["evidence_id"]]["raw"])
            for host, data in fields.items():
                record["data"].setdefault(host, {}).update(data)
                result["address_fragment"].setdefault(host, {}).update(copy.deepcopy(data))
            # Only tokens actually observed in the source record are possessed.
            # Report payload text and a sender's current possession are not proof.
            self.research.possession[self.bindings[recipient]].update(token_refs(fields))
        result["view"] = self.views()[recipient]
        return result

    def construct(self, actor, proposal):
        label = proposal.get("action", "Sleep")
        if proposal.get("source_host"):
            own = self.sessions(actor).get(proposal.get("session", 0))
            if not own or own.hostname != proposal["source_host"]:
                raise ValueError("Task source does not match this actor's owned session")
        if label == "ExploitRemoteService":
            raise ValueError("Research profile requires explicit AttemptAccess method")
        if label not in ("Probe", "InspectArtifacts", "AttemptAccess"):
            # Pivot is enabled through the compiled native ACL recipe. The old
            # adapter's settings gate is historical and therefore handled here.
            if label == "EstablishPivot":
                from packages.engine_worker.cc4.routes import EstablishPivot
                source = self.sessions(actor).get(proposal.get("session", 0))
                host = proposal.get("target")
                if not source or not source.active or not hasattr(source, "ports") or not any(s.active and s.hostname == host and s.has_privileged_access() and not hasattr(s, "ports") for s in self.sessions(actor).values()):
                    raise ValueError("Pivot requires an owned controller and privileged owned shell")
                return EstablishPivot(session=proposal.get("session", 0), agent=self.bindings[actor], hostname=host)
            return super().construct(actor, proposal)
        sid = proposal.get("session", 0)
        source = self.sessions(actor).get(sid)
        if not source or not source.active:
            raise ValueError("Action requires an active actor-owned session")
        target = proposal.get("target")
        if label == "InspectArtifacts":
            if target != source.hostname:
                raise ValueError("Artifact inspection must use an owned local session")
            return InspectArtifacts(sid, self.bindings[actor], target)
        view = self.views()[actor]
        if not hasattr(source, "ports") or target not in view["known"]["ip_address"]:
            raise ValueError("Remote action requires an owned controller and observed address")
        action = (Probe if label == "Probe" else AttemptAccess)(sid, self.bindings[actor], IPv4Address(target))
        if label == "Probe":
            kind, port = proposal.get("probe"), proposal.get("port")
            if kind not in PUBLIC_CATALOG["probes"] or port not in (22, 80) or kind == "service_behavior" and port != 80 or kind == "auth_policy" and port != 22:
                raise ValueError("Unsupported probe/protocol combination")
            action.probe_kind, action.selected_port = kind, port
            action.duration = PUBLIC_CATALOG["probes"][kind]["duration"]
        else:
            method = proposal.get("method")
            if method not in PUBLIC_CATALOG["methods"]:
                raise ValueError("Select an explicit supported method")
            if IPv4Address(target) not in source.ports:
                raise ValueError("Access requires this controller's own service scan")
            if method == "credential_login" and proposal.get("token_ref") not in self.research.possession[self.bindings[actor]]:
                raise ValueError("Credential login requires a possessed token reference")
            action.method, action.token_ref = method, proposal.get("token_ref")
            action.duration = PUBLIC_CATALOG["methods"][method]["duration"]
        checked = self.controller.replace_action_if_invalid(action, self.controller.agent_interfaces[self.bindings[actor]])
        if type(checked).__name__ == "InvalidAction":
            raise ValueError("Native action-space validation rejected the action")
        if label == "AttemptAccess":
            action.attempt_id = self.research.reserve(self.bindings[actor], proposal, self.tick + 1)
        return action

    def preconditions(self, view, proposal):
        label = proposal.get("action", "Sleep")
        if label not in ("Probe", "InspectArtifacts", "AttemptAccess"):
            return super().preconditions(view, proposal)
        sid = proposal.get("session", 0)
        own = next((s for s in view["sessions"] if s["id"] == sid and s["active"]), None)
        if label == "InspectArtifacts":
            return {"active_owned_local_session": bool(own and own["hostname"] == proposal.get("target"))}
        checks = {"active_owned_controller": bool(own and own["controller"]),
                  "observed_target": proposal.get("target") in view["known"]["ip_address"]}
        if label == "AttemptAccess":
            checks["own_service_scan"] = proposal.get("target") in view["scan_cache"].get(str(sid), {})
            checks["selected_method"] = proposal.get("method") in PUBLIC_CATALOG["methods"]
            if proposal.get("method") == "credential_login":
                checks["token_possessed"] = proposal.get("token_ref") in view["possessed_tokens"]
        return checks

    def step(self, proposals):
        result = super().step(proposals)
        result["defender_events"].extend(self.response.complete(result["execution_trace"], self.tick))
        for record in result["actions"]:
            if record["proposal"].get("action") == "AttemptAccess" and record["valid"] and record["lifecycle"] == "completed":
                for attempt in self.research.attempts:
                    if attempt["actor"] == self.bindings[record["actor"]] and attempt["admitted_tick"] == record["started_tick"]:
                        attempt.update(status="completed", completed_tick=self.tick, outcome=record["outcome"])
                        record["attempt_id"] = attempt["id"]
        result["views"] = self.views()
        result["truth"] = self.snapshot()
        return result
