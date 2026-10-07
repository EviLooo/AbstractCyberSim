"""Opt-in host ACL recipe on native CC4 hosts; no agent-visible route oracle."""
import copy
import random

from CybORG.Shared import Observation
from CybORG.Shared.Enums import ProcessName, ProcessType, SessionType
from CybORG.Shared.Session import RedAbstractSession
from CybORG.Simulator.Actions import Action
from CybORG.Simulator.Process import Process
from CybORG.Simulator.Service import Service
from packages.contracts.route_templates import templates

FOOTHOLD = "contractor_network_subnet_user_host_0"
ZONES = ["restricted_zone_a_subnet", "restricted_zone_b_subnet",
         "operational_zone_a_subnet", "operational_zone_b_subnet",
         "public_access_zone_subnet", "admin_network_subnet", "office_network_subnet"]


def settings(config):
    return (config["scenario"].get("complexity") or {}).get("routes") or {"enabled": False}


def materialize(scenario, config):
    options = settings(config)
    if not options["enabled"]:
        return {"enabled": False}
    # Separate stream: changing branch count cannot perturb native population.
    rng = random.Random("routes:1.0:{}".format(config["scenario"]["world_seed"]))
    zones = ZONES[:]
    rng.shuffle(zones)
    zones = ["contractor_network_subnet"] + zones[:options["depth"] - 1]
    layers, dead_ends, rules = [], [], []
    tradeoffs = options.get("tradeoffs") or {"enabled": False}
    route_templates = templates(tradeoffs) if tradeoffs["enabled"] else {}
    template_rng = random.Random("route-templates:1.0:{}".format(config["scenario"]["world_seed"]))
    variants = ["fast_ssh", "quiet_ftp"] + (["privileged_ftp"] if tradeoffs.get("privileged_route") else [])
    sources = [FOOTHOLD]
    for level, zone in enumerate(zones):
        indices = list(range(1, config["scenario"]["cc4"]["user_hosts"]))
        rng.shuffle(indices)
        gateways = ["{}_user_host_{}".format(zone, i) for i in indices[:options["alternatives"]]]
        assignment = [variants[i % len(variants)] for i in range(len(gateways))]
        template_rng.shuffle(assignment)
        # One extra native host per layer; same reachable SSH port, strong account.
        dead = "contractor_network_subnet_server_host_0" if level == 0 else zone + "_user_host_0"
        candidates = gateways + ([dead] if options["hardened_dead_end"] else [])
        for hostname in candidates:
            host = scenario.hosts[hostname]
            host.services = {k: v for k, v in host.services.items() if k == ProcessName.SSHD}
            host.processes = [p for p in host.processes if p.name == ProcessName.SSHD]
            host.default_processes = host.processes.copy()
            for user in host.users:
                user.bruteforceable = hostname != dead and user.username == "user"
            rule = {"target": hostname, "allowed_sources": sources[:],
                    "template": "strong_ssh_account" if hostname == dead else "weak_ssh_account"}
            if tradeoffs["enabled"] and hostname in gateways:
                variant = assignment[gateways.index(hostname)]
                specification = copy.deepcopy(route_templates[variant])
                if specification["service"] == "FTP":
                    # Reuse an already reserved PID: template RNG never consumes
                    # native population randomness. Native FTPDirectoryTraversal
                    # checks the FEMITTER process and creates a real owned session.
                    pid = host.processes[0].pid
                    process = Process(process_name="FTP", pid=pid, username=specification["privilege"],
                                      path="/usr/sbin", process_type=ProcessType.FEMITTER,
                                      open_ports=[{"local_address": "0.0.0.0", "local_port": 21}])
                    host.services = {"FTP": Service(process=pid)}
                    host.processes = [process]
                    host.default_processes = host.processes.copy()
                    for user in host.users:
                        user.bruteforceable = False
                rule.update(template=variant, tradeoff=specification)
            rules.append(rule)
        layers.append(gateways)
        if options["hardened_dead_end"]:
            dead_ends.append(dead)
        sources = gateways
    targets = list(config["scenario"]["targets"])
    overlap = set(targets) & set(dead_ends)
    if overlap:
        raise ValueError("Mission target cannot be a hardened route dead end")
    for hostname in targets:
        rules.append({"target": hostname, "allowed_sources": sources[:], "template": "native_target"})
    # Native ExploreHost reads this inventory only after privilege escalation.
    # It contains addresses, not ACLs, vulnerability labels or a winning route.
    for level, gateways in enumerate(layers):
        next_hosts = layers[level + 1] if level + 1 < len(layers) else targets
        if level + 1 < len(layers) and options["hardened_dead_end"]:
            next_hosts = next_hosts + [dead_ends[level + 1]]
        for hostname in gateways:
            scenario.hosts[hostname].info.update({h: {"Interfaces": "ip_address"} for h in next_hosts})
    return {"enabled": True, "version": "1.0", "settings": copy.deepcopy(options),
            "foothold": FOOTHOLD, "layers": layers, "dead_ends": dead_ends,
            "rules": rules, "enforcement": "native RemoteAction host-source blocks",
            "monitoring_boundary": "No native Blue coverage in contractor subnet; later layers use native Blue territories",
            "discovery_boundary": "ICMP discovery is not blocked by these service-access rules",
            "pivot": "EstablishPivot extension; privileged owned shell; two ticks; empty cache",
            "tradeoffs": {"enabled": tradeoffs["enabled"], "version": "1.0",
                          "settings": copy.deepcopy(tradeoffs),
                          "sensor": "Separate synthetic gateway traffic sensor; distinct from native Blue Monitor",
                          "effect": "Temporary native incoming/outgoing service ACL block; sessions and ICMP remain"}}


def install_blocks(state, manifest):
    if manifest["enabled"]:
        for rule in manifest["rules"]:
            state.blocks[rule["target"]] = sorted(set(state.hosts) - set(rule["allowed_sources"]) - {rule["target"]})


class EstablishPivot(Action):
    """Explicit simulated implant deployment. Does not grant access or privilege.

    Converts an existing privileged shell in place to a native controller. Same
    PID, ownership, parent, children and ID; new local scan cache. Native Restore
    still removes it. This capability is our extension, not stock CC4 behavior.
    """
    def __init__(self, session: int, agent: str, hostname: str):
        super().__init__()
        self.session, self.agent, self.hostname = session, agent, hostname
        self.duration = 2

    def execute(self, state):
        own = state.sessions[self.agent]
        source = own.get(self.session)
        eligible = [s for s in own.values() if s.hostname == self.hostname and s.active
                    and s.has_privileged_access() and not s.is_escalate_sandbox]
        if not source or not source.active or not isinstance(source, RedAbstractSession) or not eligible:
            return Observation(False)
        shell = sorted(eligible, key=lambda s: s.ident)[0]
        if isinstance(shell, RedAbstractSession):
            return Observation(False)
        pivot = RedAbstractSession(shell.ident, shell.hostname, shell.username, shell.agent, shell.pid)
        pivot.__dict__.update(copy.copy(shell.__dict__))
        pivot.session_type = SessionType.RED_ABSTRACT_SESSION
        pivot.ports, pivot.operating_system, pivot.ot_service = {}, {}, None
        own[shell.ident] = pivot
        if shell.parent in own:
            own[shell.parent].children[shell.ident] = pivot
        obs = Observation(True)
        obs.add_session_info(hostid=self.hostname, **pivot.get_state())
        return obs

    def __str__(self):
        return "EstablishPivot {}".format(self.hostname)
