"""Research worker layout over CC4's native enterprise templates."""
import copy

from CybORG.Agents import SleepAgent
from CybORG.Simulator.Actions import Sleep, Monitor
from CybORG.Simulator.Actions.ConcreteActions.RedSessionCheck import RedSessionCheck
from CybORG.Simulator.Scenarios import EnterpriseScenarioGenerator
from packages.engine_worker.cc4.routes import materialize, EstablishPivot

FOOTHOLD = "contractor_network_subnet_user_host_0"


class ResearchScenario(EnterpriseScenarioGenerator):
    def __init__(self, config):
        self.config = config
        options = config["scenario"]["cc4"]
        self.MIN_USER_HOSTS = self.MAX_USER_HOSTS = options["user_hosts"]
        self.MIN_SERVER_HOSTS = self.MAX_SERVER_HOSTS = options["server_hosts"]
        self.MAX_ADDON_SERVICES = options["addon_services"]
        super().__init__(blue_agent_class=SleepAgent, red_agent_class=SleepAgent,
                         green_agent_class=SleepAgent, steps=config["schedule"]["max_ticks"])

    def create_scenario(self, np_random):
        scenario = super().create_scenario(np_random)
        self.route_manifest = materialize(scenario, self.config)
        template = copy.deepcopy(scenario.agents["red_agent_0"])
        zones = sorted({zone for name, actor in scenario.agents.items()
                        if name.startswith("red_agent_") for zone in actor.allowed_subnets})
        for name in list(scenario.agents):
            if name.startswith("red_agent_"):
                del scenario.agents[name]
        names = ["red_agent_{}".format(i) for i in range(self.config["team"]["workers"])]
        for name in names:
            actor = copy.deepcopy(template)
            if self.route_manifest["enabled"]:
                actor.actions = actor.actions + [EstablishPivot]
            actor.name = name
            actor.allowed_subnets = list(zones)
            actor.agent_type = SleepAgent(name)
            actor.internal_only = False
            actor.osint = {"Hosts": {FOOTHOLD: {"Interfaces": "All", "System info": "All", "User info": "All"}}}
            actor.default_actions = (RedSessionCheck, {"session": 0, "agent": name})
            for session in actor.starting_sessions:
                session.name = name + "_foothold"
                session.hostname = FOOTHOLD
            scenario.agents[name] = actor
        scenario.team_agents["Red"] = names
        for name, actor in scenario.agents.items():
            if name.startswith("blue_"):
                actor.default_actions = (Sleep, {}) if self.config["scenario"]["defender"] == "passive" else (Monitor, {"session": 0, "agent": name})
        for target in self.config["scenario"]["targets"]:
            if target not in scenario.hosts or target == FOOTHOLD or "_router" in target:
                raise ValueError("Mission requires a generated non-router target distinct from initial access")
        # No Green actions/phishing and no extra respawn hook are enabled in
        # this profile. Total access loss is a mission failure, not free recovery.
        self.validate_scenario(scenario)
        return scenario
