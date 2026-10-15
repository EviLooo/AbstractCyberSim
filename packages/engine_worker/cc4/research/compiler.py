"""Finite recipes over native CC4 hosts, independent of team architecture.

Role names/conditions/witnesses are privileged researcher metadata. Hostnames
are native bindings; no generated complete route enters observations.
"""
import copy
import hashlib
import random

from CybORG.Shared.Enums import ProcessType
from CybORG.Simulator.Process import Process
from CybORG.Simulator.Service import Service
from CybORG.Simulator.Actions import Sleep, DiscoverRemoteSystems, AggressiveServiceDiscovery, PrivilegeEscalate
from packages.engine_worker.cc4.scenario import ResearchScenario, FOOTHOLD
from packages.engine_worker.cc4.routes import EstablishPivot
from packages.engine_worker.cc4.research.actions import Probe, InspectArtifacts, AttemptAccess
from packages.engine_worker.cc4.research.changes import PatchService
from CybORG.Simulator.Actions import Monitor

TARGET_A = "restricted_zone_a_subnet_server_host_0"
TARGET_B = "operational_zone_a_subnet_server_host_0"


class InvestigationScenario(ResearchScenario):
    def create_scenario(self, np_random):
        scenario = super().create_scenario(np_random)
        options = self.config["scenario"]["research"]
        # Hold the stock mission policy fixed for this explicit research
        # profile. Historical CC4 still uses its original three-phase clock.
        scenario.mission_phases = (self.config["schedule"]["max_ticks"], 0, 0)
        fixed = copy.deepcopy(scenario.allowed_subnets_per_mphase[0])
        scenario.allowed_subnets_per_mphase = {phase: copy.deepcopy(fixed) for phase in range(3)}
        rng = random.Random("recipe-v1:{}".format(options["seed_namespaces"]["recipe"]))
        branches = ["contractor_network_subnet_user_host_1", "contractor_network_subnet_user_host_2"]
        rng.shuffle(branches)
        roles = {"entry": FOOTHOLD, "bridge": branches[0], "archive": branches[1],
                 "app": "public_access_zone_subnet_server_host_0", "archive_target": TARGET_A,
                 "parallel_target": TARGET_B, "split_entry": "public_access_zone_subnet_user_host_0"}
        variant = options["condition_variant"]
        if variant == "seeded":
            variants = ["import_enabled", "import_disabled", "source_denied", "ssh_hardened"] if options["conditions"] == "paired" else ["import_enabled", "import_disabled"]
            variant = rng.choice(variants)
        if options["recipe"] == "linear_control":
            variant = "import_enabled"
        # No native ExploreHost wholesale inventory. Leads live in local notes.
        for host in scenario.hosts.values():
            host.info = {}
        for role, hostname in roles.items():
            host = scenario.hosts[hostname]
            if role in ("entry", "split_entry"):
                continue
            old = next(iter(host.processes))
            web_enabled = role not in ("archive", "archive_target", "parallel_target") or role == "archive_target" and variant in ("import_enabled", "source_denied") and options["recipe"] != "combine"
            account = "user"
            http = Process(process_name="http", pid=old.pid, username=account, path="/usr/sbin",
                           process_type=ProcessType.WEBSERVER, properties=["rfi"] if web_enabled else [],
                           open_ports=[{"local_address": "0.0.0.0", "local_port": 80}])
            ssh = Process(process_name="sshd", pid=max(p.pid for p in host.processes) + 1, username=account,
                          path="/usr/sbin", process_type=ProcessType.SSH,
                          open_ports=[{"local_address": "0.0.0.0", "local_port": 22}])
            host.processes = [http, ssh]
            host.default_processes = copy.deepcopy(host.processes)
            host.services = {"http": Service(process=http.pid), "sshd": Service(process=ssh.pid)}
            weak = role in ("bridge", "archive", "app") or role == "archive_target" and variant == "import_disabled" and options["recipe"] != "combine"
            for user in host.users:
                user.bruteforceable = weak and user.username == "user"
        entry_sources = [roles["entry"], roles["split_entry"]]
        rules = []
        selected = set(roles.values())
        for hostname in scenario.hosts:
            if hostname in entry_sources or "_router" in hostname or hostname == "root_internet_host_0":
                continue
            allowed = entry_sources if hostname in (roles["bridge"], roles["archive"], roles["app"]) else []
            if hostname == TARGET_A:
                allowed = [roles["bridge"]]
                if options["recipe"] != "combine" and variant != "source_denied":
                    allowed += entry_sources
            if hostname == TARGET_B:
                allowed = [roles["app"]]
            rules.append({"target": hostname, "allowed_sources": allowed, "template": "research_selected" if hostname in selected else "background_denied"})
        tokens, artifacts = {}, {}
        def note(role, suffix, content, read="user"):
            identity = hashlib.sha256("{}:{}".format(roles[role], suffix).encode()).hexdigest()[:16]
            artifacts.setdefault(roles[role], []).append({"read": read, "public": dict(content, artifact_id="note-" + identity)})
        def lead(host):
            return {"hostname": host, "address": str(next(i.ip_address for i in scenario.hosts[host].interfaces if str(i.ip_address) != "127.0.0.1"))}
        for role, target, storage in [("archive_target", TARGET_A, "archive"), ("parallel_target", TARGET_B, "app")]:
            ref = "tok-" + hashlib.sha256("{}:{}".format(options["seed_namespaces"]["recipe"], role).encode()).hexdigest()[:20]
            tokens[ref] = {"host": target, "account": "user", "valid": True}
            content = {"text": "Scheduled SSH job uses a stored account reference.", "lead": lead(target), "account": "user", "claimed_scope": target, "token_ref": ref}
            note(storage, "job", content)
            if role == "archive_target" and options["recipe"] != "combine":
                cached_ref = "tok-" + hashlib.sha256((ref + ":cached").encode()).hexdigest()[:20]
                provision = options["credential_variant"]
                if provision == "seeded":
                    provision = rng.choice(["valid", "wrong_scope", "invalid"])
                tokens[cached_ref] = {"host": TARGET_B if provision == "wrong_scope" else target,
                                      "account": "user", "valid": provision != "invalid"}
                cached = dict(content, token_ref=cached_ref,
                              text="Cached job account reference; a maintenance host stores the current record.")
                note("entry", "job", cached)
                if variant == "import_disabled":
                    note("entry", "provisioning", {"text": "Last provisioning record marked this account password weak; current validity must be checked.", "lead": lead(TARGET_A), "account": "user"})
        note("entry", "neighbors", {"text": "Administration notes mention two maintenance hosts.", "leads": [lead(roles["bridge"]), lead(roles["archive"])]})
        note("split_entry", "neighbors", {"text": "A separate maintenance notebook mentions a service host.", "leads": [lead(roles["app"]), lead(roles["archive"])]})
        note("bridge", "connection", {"text": "This host runs an SSH job to an archive.", "lead": lead(TARGET_A)})
        note("archive", "provisioning", {"text": "Maintenance account was provisioned with a weak password. Verify current reachability."})
        note("archive", "administrator", {"text": "Administrator-only maintenance inventory; this local record requires privileged access."}, read="root")
        note("entry", "parallel", {"text": "A public application appears in a maintenance note.", "lead": lead(roles["app"])})
        targets = [TARGET_A, TARGET_B] if options["recipe"] == "combine" else [TARGET_A]
        if set(self.config["scenario"]["targets"]) != set(targets):
            raise ValueError("Recipe requires targets {}".format(targets))
        self.research_manifest = {"version": "1.0", "recipe": options["recipe"], "roles": roles,
            "variant": variant, "tokens": tokens, "artifacts": artifacts,
            "attempt_limit": self.config["resources"]["team_access_attempts"], "change": options["change"],
            "feasibility": {"status": "unverified", "reason": "Native witness qualification not yet run"}}
        self.route_manifest = {"enabled": True, "version": "research-1.0", "rules": rules,
            "layers": [[roles["bridge"], roles["archive"], roles["app"]]], "dead_ends": [],
            "tradeoffs": {"enabled": False}, "foothold": FOOTHOLD,
            "enforcement": "native host-source blocks; background has no attack source"}
        for index, name in enumerate(scenario.team_agents["Red"]):
            actor = scenario.agents[name]
            actor.actions = [Sleep, DiscoverRemoteSystems, AggressiveServiceDiscovery, PrivilegeEscalate,
                             EstablishPivot, Probe, InspectArtifacts, AttemptAccess]
            start = roles["split_entry"] if options["initial_access"] == "matched_split_entry" and index % 2 else FOOTHOLD
            actor.osint = {"Hosts": {start: {"Interfaces": "All", "System info": "All"}}}
            for session in actor.starting_sessions:
                session.hostname = start
        if options["recipe"] == "recover":
            for name, actor in scenario.agents.items():
                if name.startswith("blue_"):
                    actor.actions = actor.actions + [PatchService]
                    actor.default_actions = (Monitor, {"session": 0, "agent": name})
        return scenario
