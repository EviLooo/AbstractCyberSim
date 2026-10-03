"""Read-only runtime probes used to ground the research implementation plan.

Run with the existing cyborg38 interpreter. This does not implement the study.
"""
import copy
import json
import inspect
import platform
import subprocess
import sys
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "CybORG"))

import gym
import numpy
from gym.utils import seeding
from CybORG import CybORG
from CybORG.Agents import SleepAgent
from CybORG.Shared.RewardCalculator import EmptyRewardCalculator
from CybORG.Shared.Scenarios.ScenarioGenerator import ScenarioGenerator
from CybORG.Simulator.Actions import DiscoverRemoteSystems, DiscoverNetworkServices, ExploitRemoteService, Sleep
from CybORG.Simulator.Scenarios.FileReaderScenarioGenerator import FileReaderScenarioGenerator
from CybORG.Simulator.Actions.ConcreteActions.Portscan import Portscan


class MultiRedProbeGenerator(ScenarioGenerator):
    def __init__(self, count):
        super().__init__()
        self.count = count
        self.base = FileReaderScenarioGenerator(str(ROOT / "CybORG/CybORG/Simulator/Scenarios/scenario_files/Scenario2.yaml"))

    def create_scenario(self, np_random):
        scenario = self.base.create_scenario(np_random)
        template = scenario.agents.pop("Red")
        scenario.team_agents.pop("Red")
        scenario.team_calc.pop("Red")
        names = ["Red_{}".format(i) for i in range(self.count)]
        for name in names:
            agent = copy.deepcopy(template)
            agent.name = name
            agent.team = "ResearchRed"
            agent.internal_only = False
            agent.agent_type = SleepAgent()
            for session in agent.starting_sessions:
                session.name = name + "_foothold"
            scenario.agents[name] = agent
        scenario.team_agents["ResearchRed"] = names
        scenario.team_calc["ResearchRed"] = {"probe": EmptyRewardCalculator("ResearchRed")}
        scenario.team_calc["Blue"] = {"probe": EmptyRewardCalculator("Blue")}
        self.validate_scenario(scenario)
        return scenario


def normalized(value):
    if isinstance(value, dict):
        return {str(k): normalized(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [normalized(x) for x in value]
    if hasattr(value, "tolist"):
        return normalized(value.tolist())
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def probe(count):
    env = CybORG(MultiRedProbeGenerator(count), "sim", seed=7)
    env.reset(seed=7)
    actors = [name for name in env.get_agent_ids() if name.startswith("Red_")]
    before = env.get_action_space(actors[0])
    initial_ips = {str(ip): known for ip, known in before["ip_address"].items()}
    subnet = next(subnet for subnet, known in before["subnet"].items() if known)
    actions = {a: DiscoverRemoteSystems(subnet=subnet, session=0, agent=a) for a in actors}
    obs, rewards, dones, _ = env.parallel_step(actions)
    discovered = {a: str(obs.get(a, {}).get("success")) for a in actors}
    scans = {}
    scan_targets = {}
    for actor in actors:
        known_ips = [ip for ip, known in env.get_action_space(actor)["ip_address"].items() if known]
        own_host = env.environment_controller.state.sessions[actor][0].hostname
        own_ips = {i.ip_address for i in env.environment_controller.state.hosts[own_host].interfaces}
        target = next(ip for ip in known_ips if ip not in own_ips)
        scans[actor] = DiscoverNetworkServices(session=0, agent=actor, ip_address=target)
        scan_targets[actor] = target
    obs, rewards, _, _ = env.parallel_step(scans)
    scanned = {a: str(obs.get(a, {}).get("success")) for a in actors}
    exploit_actions = {a: ExploitRemoteService(session=0, agent=a, ip_address=scan_targets[a]) for a in actors}
    obs, rewards, _, _ = env.parallel_step(exploit_actions)
    exploit_results = {a: str(obs.get(a, {}).get("success")) for a in actors}
    sessions = {a: len(env.environment_controller.state.sessions[a]) for a in actors}
    return {
        "actor_count": count,
        "hosts_including_routers": len(env.environment_controller.state.hosts),
        "active_red_actors": [a for a in env.active_agents if a in actors],
        "initial_action_space_ips": initial_ips,
        "discovery_results": discovered,
        "scan_results": scanned,
        "exploit_results": exploit_results,
        "sessions_per_actor": sessions,
        "reward_return_keys": list(rewards),
        "research_red_reward_values": [rewards[a] for a in actors],
        "message_bits": env.get_message_space(actors[0]).n,
        "warning": "Feasibility probe only; duplicated footholds, empty rewards, no comparative policies or LLMs."
    }


def probe_intel_bridge():
    env = CybORG(MultiRedProbeGenerator(2), "sim", seed=7)
    env.reset(seed=7)
    sender, recipient = "Red_0", "Red_1"
    subnet = next(k for k, known in env.get_action_space(sender)["subnet"].items() if known)
    observations, _, _, _ = env.parallel_step({
        sender: DiscoverRemoteSystems(subnet=subnet, session=0, agent=sender),
        recipient: Sleep(),
    })
    recipient_space = env.get_action_space(recipient)
    target = next(ip for ip, known in env.get_action_space(sender)["ip_address"].items()
                  if known and not recipient_space["ip_address"].get(ip, False))
    source_fragment = observations[sender][str(target)]
    fragment = {str(target): {"Interface": copy.deepcopy(source_fragment["Interface"])}}
    proposed = DiscoverNetworkServices(session=0, agent=recipient, ip_address=target)
    rejected_before = type(env.environment_controller.replace_action_if_invalid(
        proposed, env.environment_controller.agent_interfaces[recipient])).__name__
    recipient_session = env.environment_controller.state.sessions[recipient][0]
    before_sessions = len(env.environment_controller.state.sessions[recipient])
    env.environment_controller.agent_interfaces[recipient].update(fragment)
    accepted_after = type(env.environment_controller.replace_action_if_invalid(
        proposed, env.environment_controller.agent_interfaces[recipient])).__name__
    cache_present_after_bridge = target in recipient_session.ports
    observations, _, _, _ = env.parallel_step({sender: Sleep(), recipient: proposed})
    return {
        "before_verified_address_update": rejected_before,
        "after_verified_address_update": accepted_after,
        "bridge_populated_port_cache": cache_present_after_bridge,
        "recipient_scan_result": str(observations[recipient]["success"]),
        "recipient_scan_populated_own_cache": target in recipient_session.ports,
        "bridge_granted_sessions": len(env.environment_controller.state.sessions[recipient]) - before_sessions,
        "warning": "Trusted observation-fragment feasibility probe; full transport and provenance verifier not implemented."
    }


def main():
    report = {
        "python": platform.python_version(),
        "numpy": numpy.__version__,
        "gym": gym.__version__,
        "cyborg_commit": subprocess.check_output(["git", "-C", str(ROOT / "CybORG"), "rev-parse", "HEAD"], text=True).strip(),
        "probes": [],
    }
    for count in [1, 2, 4]:
        try:
            report["probes"].append(probe(count))
        except Exception as exc:
            report["probes"].append({"actor_count": count, "error": repr(exc)})
    # Test the proposed narrow compatibility fix in memory only. Restore the
    # original method afterwards; no vendor file is modified.
    original = Portscan.execute
    source = textwrap.dedent(inspect.getsource(original))
    assert source.count("state.sessions['Red']") == 2
    fixed_source = source.replace("state.sessions['Red']", "state.sessions[self.agent]")
    namespace = {}
    exec(compile(fixed_source, "<probe-only-portscan-fix>", "exec"), original.__globals__, namespace)
    report["with_temporary_portscan_fix"] = []
    try:
        Portscan.execute = namespace["execute"]
        for count in [1, 2, 4]:
            try:
                report["with_temporary_portscan_fix"].append(probe(count))
            except Exception as exc:
                report["with_temporary_portscan_fix"].append({"actor_count": count, "error": repr(exc)})
        try:
            report["verified_address_bridge_probe"] = probe_intel_bridge()
        except Exception as exc:
            report["verified_address_bridge_probe"] = {"error": repr(exc)}
    finally:
        Portscan.execute = original
    output = ROOT / "docs/research/repo-audit.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(normalized(report), indent=2), encoding="utf-8")
    print(json.dumps(normalized(report), indent=2))


if __name__ == "__main__":
    main()
