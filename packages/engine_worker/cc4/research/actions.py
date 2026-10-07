"""Minimal simulated probes, local inspection and explicit access methods.

No real exploits, authentication or network traffic occur. Effects are native
CybORG processes/sessions. Conditions are checked when a busy action completes.
"""
import copy

from CybORG.Shared import Observation
from CybORG.Simulator.Actions.Action import Action, RemoteAction
from CybORG.Simulator.Actions.ConcreteActions.ExploitActions.HTTPRFI import HTTPRFI
from CybORG.Simulator.Actions.ConcreteActions.ExploitActions.SSHBruteForce import SSHBruteForce
from CybORG.Simulator.Actions.ConcreteActions.ExploitActions.ExploitAction import ExploitAction


def source_target(action, state):
    source = state.sessions.get(action.agent, {}).get(action.session)
    target = state.ip_addresses.get(action.ip_address)
    if not source or not source.active or not target or action.dropped or action.blocked:
        return None, target
    if RemoteAction.blocking_host(state, source.hostname, target):
        return None, target
    route = RemoteAction.get_route(state, target, source.hostname)
    if route is None or any(RemoteAction.blocking_host(state, source.hostname, host) for host in route):
        return None, target
    return source, target


def listening(host, port):
    return next((p for p in host.processes if any(c.local_port == port for c in p.connections)), None)


class Probe(RemoteAction):
    def __init__(self, session, agent, ip_address):
        super().__init__(session, agent)
        self.ip_address = ip_address
        self.research_traffic = True
        self.probe_kind = "connectivity"
        self.selected_port = 80

    def execute(self, state):
        source, hostname = source_target(self, state)
        proc = listening(state.hosts[hostname], self.selected_port) if source else None
        response = "timeout"
        if proc:
            if self.probe_kind == "connectivity":
                response = "tcp_handshake"
            elif self.probe_kind == "service_behavior":
                response = "external_import_accepted" if "rfi" in proc.properties else "external_import_refused"
            else:
                response = "password_and_account_token_supported"
        obs = Observation(bool(proc))
        obs.data[str(self.ip_address)] = {"Research evidence": [{"kind": "probe", "probe": self.probe_kind,
            "port": self.selected_port, "source_host": state.sessions.get(self.agent, {}).get(self.session).hostname if state.sessions.get(self.agent, {}).get(self.session) else None,
            "response": response}]}
        return obs

    def __str__(self):
        return "Probe {} {} {}".format(self.probe_kind, self.selected_port, self.ip_address)


class InspectArtifacts(Action):
    def __init__(self, target_session, agent, hostname):
        super().__init__()
        # Native ActionSpace distinguishes server/controller `session` from
        # client/shell `target_session`. Inspection is legal from either owned
        # type; our gateway and completion predicate enforce local ownership.
        self.target_session, self.agent, self.hostname = target_session, agent, hostname
        self.duration = 2

    def execute(self, state):
        owned = state.sessions.get(self.agent, {}).get(self.target_session)
        if not owned or not owned.active or owned.hostname != self.hostname:
            return Observation(False)
        artifacts = state.research.local_artifacts(self.agent, self.hostname, owned.has_privileged_access())
        obs = Observation(True)
        obs.data[self.hostname] = {"Research evidence": [{"kind": "artifact", **a} for a in artifacts]}
        for artifact in artifacts:
            for lead in artifact.get("leads", []) + ([artifact["lead"]] if artifact.get("lead") else []):
                obs.add_interface_info(hostid=lead["address"], ip_address=lead["address"])
                obs.add_system_info(hostid=lead["address"], hostname=lead["hostname"])
        return obs

    def __str__(self):
        return "InspectArtifacts {}".format(self.hostname)


class CredentialLogin(ExploitAction):
    PORT = 22

    def execute(self, state):
        source, hostname = source_target(self, state)
        obs = Observation(False)
        if not source or self.ip_address not in source.ports:
            return obs
        if not state.research.permits(self.agent, self.token_ref, hostname):
            return obs
        data = self._get_exploit_data(state, "ssh")
        if not data.get("vuln_proc"):
            return obs
        # A per-action copy avoids mutating the shared listening service account.
        data["vuln_proc"] = copy.copy(data["vuln_proc"])
        data["vuln_proc"].user = state.research.tokens[self.token_ref]["account"]
        port = data["target_host"].get_ephemeral_port()
        session = self._create_new_session(state, obs, port, session_type="SSH", **data)
        self._create_new_session_event(session, port, **data)
        obs.add_session_info(**self._get_session_info(session))
        obs.add_system_info(**self._get_system_info(data["target_host"]))
        obs.set_success(True)
        return obs


class AttemptAccess(RemoteAction):
    def __init__(self, session, agent, ip_address):
        super().__init__(session, agent)
        self.ip_address = ip_address
        self.research_traffic = True
        self.method = "web_rfi"
        self.token_ref = None
        self.duration = 4

    def execute(self, state):
        source, hostname = source_target(self, state)
        obs = Observation(False)
        # Scan possession, current reachability and account conditions are all
        # checked at completion, including a Restore during native busy time.
        attackable = set(state.research.manifest["roles"].values()) - {
            state.research.manifest["roles"]["entry"], state.research.manifest["roles"]["split_entry"]}
        if source and hostname in attackable and self.ip_address in getattr(source, "ports", {}):
            kind = {"web_rfi": HTTPRFI, "ssh_weak_auth": SSHBruteForce, "credential_login": CredentialLogin}[self.method]
            self.sub_action = kind(session=self.session, agent=self.agent, ip_address=self.ip_address)
            self.sub_action.token_ref = self.token_ref
            self.sub_action.dropped, self.sub_action.blocked = self.dropped, self.blocked
            self.sub_action.route, self.sub_action.route_designated = self.route, self.route_designated
            obs = self.sub_action.execute(state)
        # This is an outcome, not a hidden failure-cause label.
        obs.data.setdefault(str(self.ip_address), {})["Research evidence"] = [{"kind": "access_result",
            "method": self.method, "source_host": source.hostname if source else None,
            "response": "access_established" if obs.action_succeeded else "access_not_established"}]
        return obs

    def __str__(self):
        return "AttemptAccess {} {}".format(self.method, self.ip_address)
