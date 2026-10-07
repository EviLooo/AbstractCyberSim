"""Bounded CC4 integration fixtures; no providers, training or research evaluation.

Run in an isolated Python 3.12 environment with --checkout pointing to the
unmodified CC4 repository. Each fixture constructs and discards its own world.
"""
from __future__ import annotations

import argparse
import copy
import importlib.metadata
import json
import platform
import subprocess
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkout", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    checkout = args.checkout.resolve()
    sys.path.insert(0, str(checkout))
    import CybORG as module
    from CybORG import CybORG
    from CybORG.Agents import SleepAgent
    from CybORG.Shared.Session import RedAbstractSession
    from CybORG.Simulator.Scenarios import EnterpriseScenarioGenerator
    from CybORG.Simulator.Actions import (
        Sleep, DiscoverRemoteSystems, AggressiveServiceDiscovery,
        ExploitRemoteService, PrivilegeEscalate, Restore,
    )
    from CybORG.Simulator.Actions.ConcreteActions.RedSessionCheck import RedSessionCheck
    from CybORG.Simulator.Actions.ConcreteActions.ControlTraffic import BlockTrafficZone, AllowTrafficZone

    assert Path(module.__file__).resolve().is_relative_to(checkout)

    class ResearchGenerator(EnterpriseScenarioGenerator):
        """Audit-only configuration: mobile workers, equal contractor footholds.

        All worker allowed-subnet lists contain every non-internet zone. This
        avoids native zone reassignment without changing upstream controller code.
        Blue/Green sleep here to isolate actor semantics; their *end-turn* hooks
        still run. This is a compatibility fixture, not a validated research world.
        """
        def __init__(self, count):
            super().__init__(blue_agent_class=SleepAgent, red_agent_class=SleepAgent,
                             green_agent_class=SleepAgent, steps=60)
            self.count = count

        def create_scenario(self, np_random):
            scenario = super().create_scenario(np_random)
            template = copy.deepcopy(scenario.agents["red_agent_0"])
            # Fixed equal foothold, distinct from the target used by the fixture.
            initial_host = "contractor_network_subnet_user_host_0"
            template.osint = {"Hosts": {initial_host: {
                "Interfaces": "All", "System info": "All", "User info": "All"}}}
            for session in template.starting_sessions:
                session.hostname = initial_host
            zones = sorted({zone for name, actor in scenario.agents.items()
                            if name.startswith("red_agent_")
                            for zone in actor.allowed_subnets})
            for name in list(scenario.agents):
                if name.startswith("red_agent_"):
                    del scenario.agents[name]
            names = [f"red_agent_{index}" for index in range(self.count)]
            for name in names:
                actor = copy.deepcopy(template)
                actor.name = name
                actor.allowed_subnets = list(zones)
                actor.agent_type = SleepAgent(name)
                actor.default_actions = (RedSessionCheck, {"session": 0, "agent": name})
                for session in actor.starting_sessions:
                    session.name = name + "_foothold"
                scenario.agents[name] = actor
            scenario.team_agents["Red"] = names
            self.validate_scenario(scenario)
            return scenario

    checks = []
    def record(name, callback):
        try:
            details = callback()
            checks.append({"name": name, "status": "pass", "details": details})
        except Exception as error:
            import traceback
            checks.append({"name": name, "status": "fail", "error": str(error),
                           "traceback": traceback.format_exc()})

    def make(generator=None):
        generator = generator or EnterpriseScenarioGenerator(
            blue_agent_class=SleepAgent, red_agent_class=SleepAgent,
            green_agent_class=SleepAgent, steps=60)
        return CybORG(generator, seed=100)

    def finish(env, actions):
        """Submit once and wait for stock durations; never skip action validity."""
        observations, _, _, _ = env.parallel_step(actions=actions)
        for _ in range(8):
            pending = env.environment_controller.actions_in_progress
            if not any(pending.get(name) for name in actions):
                return observations
            observations, _, _, _ = env.parallel_step()
        raise AssertionError("fixture exceeded eight continuation ticks")

    def native_layout():
        env = make()
        controller = env.environment_controller
        reds = [name for name in controller.agent_interfaces if name.startswith("red_")]
        active = [name for name in env.active_agents if name.startswith("red_")]
        assert len(reds) == 6 and active == ["red_agent_0"]
        space = env.get_action_space("red_agent_0")
        false_ips = [str(ip) for ip, known in space["ip_address"].items() if not known]
        known_ips = [str(ip) for ip, known in space["ip_address"].items() if known]
        assert false_ips and len(known_ips) < len(controller.state.hosts)
        return {"hosts": len(controller.state.hosts), "red_identities": reds,
                "active_reds": active, "known_ips": known_ips,
                "hidden_ip_keys_present": len(false_ips),
                "requirement": "filter known=False keys before policy/UI exposure"}

    def workers(count):
        env = make(ResearchGenerator(count))
        controller = env.environment_controller
        names = [f"red_agent_{i}" for i in range(count)]
        target = "contractor_network_subnet_server_host_0"
        assert all(s.hostname != target for name in names
                   for s in controller.state.sessions[name].values()), "target is already a foothold"
        target_ip = controller.state.hostname_ip_map[target]
        subnet = controller.state.subnet_name_to_cidr[
            controller.state.hostname_subnet_map[target]]
        before_tick = controller.step_count
        finish(env, {name: DiscoverRemoteSystems(subnet=subnet, session=0, agent=name)
                     for name in names})
        discovery_ticks = controller.step_count - before_tick
        assert discovery_ticks == 1
        assert all(env.get_action_space(name)["ip_address"][target_ip] for name in names)
        # Discovering an address does not populate other workers' exploit caches.
        finish(env, {names[0]: AggressiveServiceDiscovery(
            session=0, agent=names[0], ip_address=target_ip)})
        first_ports = dict(controller.state.sessions[names[0]][0].ports)
        assert target_ip in first_ports
        if count > 1:
            assert target_ip not in controller.state.sessions[names[1]][0].ports
        finish(env, {name: AggressiveServiceDiscovery(session=0, agent=name, ip_address=target_ip)
                     for name in names[1:]})
        actions = {name: ExploitRemoteService(session=0, agent=name, ip_address=target_ip)
                   for name in names}
        duration = max(action.duration for action in actions.values())
        before_tick = controller.step_count
        observations = finish(env, actions)
        assert controller.step_count - before_tick == duration
        attempts = {name: [str(observations[name]["success"])] for name in names}
        # Native selection is stochastic. Retry failed attempts, at most three
        # times; report every outcome rather than presuming attacks must succeed.
        for _ in range(3):
            missing = [name for name in names if not any(s.hostname == target
                       for s in controller.state.sessions[name].values())]
            if not missing:
                break
            retry = {name: ExploitRemoteService(session=0, agent=name, ip_address=target_ip)
                     for name in missing}
            retry_obs = finish(env, retry)
            for name in missing:
                attempts[name].append(str(retry_obs[name]["success"]))
        sessions = {}
        for name in names:
            owned = [session for session in controller.state.sessions[name].values()
                     if session.hostname == target]
            assert owned and all(session.agent == name for session in owned)
            sessions[name] = [session.ident for session in owned]
        return {"worker_count": count, "hosts": len(controller.state.hosts),
                "joint_discovery_ticks": discovery_ticks, "exploit_duration": duration,
                "owned_target_sessions": sessions, "exploit_outcomes": attempts,
                "scan_cache_private": True,
                "fixture": "custom generator, stock controller/actions, sleeping policies"}

    def cross_zone(custom):
        env = make(ResearchGenerator(2) if custom else None)
        c = env.environment_controller
        attacker = "red_agent_0"
        contractor = "contractor_network_subnet_server_host_0"
        destination = "restricted_zone_a_subnet_server_host_0"
        contractor_ip = c.state.hostname_ip_map[contractor]
        destination_ip = c.state.hostname_ip_map[destination]
        subnet = c.state.subnet_name_to_cidr[c.state.hostname_subnet_map[contractor]]
        # Target truth is fixture oracle only. Verify addresses become known
        # through legal native discoveries/escalation before using them.
        finish(env, {attacker: DiscoverRemoteSystems(session=0, agent=attacker, subnet=subnet)})
        assert env.get_action_space(attacker)["ip_address"][contractor_ip]
        finish(env, {attacker: AggressiveServiceDiscovery(session=0, agent=attacker, ip_address=contractor_ip)})
        contractor_attempts = []
        for _ in range(4):
            obs = finish(env, {attacker: ExploitRemoteService(session=0, agent=attacker, ip_address=contractor_ip)})
            contractor_attempts.append(str(obs[attacker]["success"]))
            if any(s.hostname == contractor for s in c.state.sessions[attacker].values()):
                break
        assert any(s.hostname == contractor for s in c.state.sessions[attacker].values()), contractor_attempts
        finish(env, {attacker: PrivilegeEscalate(session=0, agent=attacker, hostname=contractor)})
        assert env.get_action_space(attacker)["ip_address"][destination_ip]
        finish(env, {attacker: AggressiveServiceDiscovery(session=0, agent=attacker, ip_address=destination_ip)})
        destination_attempts = []
        for _ in range(4):
            observations = finish(env, {attacker: ExploitRemoteService(session=0, agent=attacker, ip_address=destination_ip)})
            destination_attempts.append(str(observations[attacker]["success"]))
            if any(s.hostname == destination for name, sessions in c.state.sessions.items()
                   if name.startswith("red_") for s in sessions.values()):
                break
        owners = [name for name, sessions in c.state.sessions.items()
                  if name.startswith("red_") and any(s.hostname == destination for s in sessions.values())]
        assert owners == ([attacker] if custom else ["red_agent_1"])
        result = {"custom_generator": custom, "destination_owner": owners,
                  "contractor_exploit_outcomes": contractor_attempts,
                  "destination_exploit_outcomes": destination_attempts,
                  "automatic_zone_handover": not custom,
                  "recipient_observation_present": "red_agent_1" in observations}
        recipient_knows = env.get_action_space("red_agent_1")["ip_address"][destination_ip]
        assert bool(recipient_knows) is (not custom)
        result["other_worker_automatically_knows_destination"] = bool(recipient_knows)
        # Exercise real five-tick recovery only in the stock territorial fixture.
        if not custom:
            blue = "blue_agent_0"
            action = Restore(session=0, agent=blue, hostname=destination)
            before_tick = c.step_count
            finish(env, {blue: action})
            assert c.step_count - before_tick == 5
            assert not any(s.hostname == destination for s in c.state.sessions["red_agent_1"].values())
            result.update({"restore_ticks": 5, "restore_removed_red_sessions": True})
            blocked = finish(env, {blue: BlockTrafficZone(session=0, agent=blue,
                from_subnet="contractor_network_subnet", to_subnet="restricted_zone_a_subnet")})
            assert blocked[blue]["success"] == True
            denied = finish(env, {attacker: AggressiveServiceDiscovery(
                session=0, agent=attacker, ip_address=destination_ip)})
            assert denied[attacker]["success"] == False
            allowed = finish(env, {blue: AllowTrafficZone(session=0, agent=blue,
                from_subnet="contractor_network_subnet", to_subnet="restricted_zone_a_subnet")})
            assert allowed[blue]["success"] == True
            reachable = finish(env, {attacker: AggressiveServiceDiscovery(
                session=0, agent=attacker, ip_address=destination_ip)})
            assert reachable[attacker]["success"] == True
            result.update({"block_denied_scan": True, "allow_restored_scan": True})
        return result

    def verified_address_bridge():
        env = make(ResearchGenerator(2))
        c = env.environment_controller
        sender, recipient = "red_agent_0", "red_agent_1"
        target = "contractor_network_subnet_server_host_0"
        address = c.state.hostname_ip_map[target]
        subnet = c.state.subnet_name_to_cidr[c.state.hostname_subnet_map[target]]
        assert not env.get_action_space(recipient)["ip_address"][address]
        observations = finish(env, {sender: DiscoverRemoteSystems(
            session=0, agent=sender, subnet=subnet)})
        assert env.get_action_space(sender)["ip_address"][address]
        assert not env.get_action_space(recipient)["ip_address"][address]
        assert str(address) in observations[sender]
        # Adapter must validate provenance before calling this hook. The fixture
        # forwards only an address proven by the sender's native observation.
        before_sessions = len(c.state.sessions[recipient])
        c.agent_interfaces[recipient].update({str(address): {
            "Interface": [{"ip_address": address}]}})
        assert env.get_action_space(recipient)["ip_address"][address]
        assert len(c.state.sessions[recipient]) == before_sessions
        assert address not in c.state.sessions[recipient][0].ports
        scan = finish(env, {recipient: AggressiveServiceDiscovery(
            session=0, agent=recipient, ip_address=address)})
        assert scan[recipient]["success"] == True
        assert address in c.state.sessions[recipient][0].ports
        return {"sender_discovery_not_automatically_shared": True,
                "verified_interface_update_unlocks_scan": True,
                "update_grants_no_sessions_or_ports": True}

    def phases():
        env = make(EnterpriseScenarioGenerator(blue_agent_class=SleepAgent,
                   red_agent_class=SleepAgent, green_agent_class=SleepAgent, steps=9))
        c = env.environment_controller
        greens = [name for name in c.agent_interfaces if name.startswith("green_")]
        changes = []
        blocking = repr(c.state.blocks)
        for _ in range(9):
            env.parallel_step()
            changes.append({"phase": c.state.mission_phase,
                "green_allowed_subnets": {name: list(c.agent_interfaces[name].allowed_subnets)
                                          for name in greens}})
            assert repr(c.state.blocks) == blocking
        assert [x["phase"] for x in changes] == [0, 0, 0, 1, 1, 1, 2, 2, 2]
        assert changes[0]["green_allowed_subnets"] != changes[3]["green_allowed_subnets"]
        return {"phases": [x["phase"] for x in changes], "green_permissions_changed": True,
                "blocks_unchanged": True, "meaning": "intended policy changes; no automatic firewall enforcement"}

    record("stock_layout_and_hidden_keys", native_layout)
    for count in (1, 2, 4, 8):
        record(f"external_workers_{count}", lambda count=count: workers(count))
    record("stock_handover_and_five_tick_restore", lambda: cross_zone(False))
    record("custom_mobile_worker_cross_zone", lambda: cross_zone(True))
    record("verified_address_delivery_hook", verified_address_bridge)
    record("mission_phase_policy_semantics", phases)
    result = {
        "purpose": "bounded software compatibility fixtures; not research experiments",
        "upstream_url": "https://github.com/cage-challenge/cage-challenge-4",
        "upstream_commit": subprocess.check_output(["git", "-C", str(checkout), "rev-parse", "HEAD"], text=True).strip(),
        "upstream_dirty": bool(subprocess.check_output(["git", "-C", str(checkout), "status", "--porcelain"], text=True).strip()),
        "python": platform.python_version(),
        "packages": {name: importlib.metadata.version(name) for name in
                     ("numpy", "gym", "gymnasium", "networkx", "pygame", "PyYAML")},
        "checks": checks,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"checks": [{"name": x["name"], "status": x["status"],
                                 "error": x.get("error")} for x in checks]}, indent=2))
    return int(any(check["status"] != "pass" for check in checks))


if __name__ == "__main__":
    raise SystemExit(main())
