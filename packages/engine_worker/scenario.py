"""Native scenario construction. No cognition or UI dependencies belong here."""
import copy
from pathlib import Path

from CybORG.Agents import SleepAgent
from CybORG.Shared.RewardCalculator import EmptyRewardCalculator
from CybORG.Shared.Scenarios.ScenarioGenerator import ScenarioGenerator
from CybORG.Simulator.Actions import Monitor, Sleep
from CybORG.Simulator.Scenarios.FileReaderScenarioGenerator import FileReaderScenarioGenerator

ROOT = Path(__file__).resolve().parents[2]


class EnterpriseScenario(ScenarioGenerator):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.base = FileReaderScenarioGenerator(str(ROOT / "CybORG/CybORG/Simulator/Scenarios/scenario_files/Scenario2.yaml"))

    def create_scenario(self, np_random):
        scenario = self.base.create_scenario(np_random)
        template = scenario.agents.pop("Red")
        scenario.team_agents.pop("Red")
        scenario.team_calc.pop("Red")
        names = ["Red_{}".format(i) for i in range(self.config["team"]["workers"])]
        for name in names:
            actor = copy.deepcopy(template)
            actor.name = name
            actor.team = "ResearchRed"
            actor.internal_only = False
            actor.agent_type = SleepAgent()
            actor.default_actions = (Sleep, {})
            for session in actor.starting_sessions:
                session.name = name + "_foothold"
            scenario.agents[name] = actor
        scenario.team_agents["ResearchRed"] = names
        scenario.team_calc["ResearchRed"] = {"empty": EmptyRewardCalculator("ResearchRed")}
        # Legacy reward calculators assume one actor named Red. We use an
        # independent deduplicated mission evaluator, never their duplicated values.
        for team in ["Blue", "Green"]:
            if team in scenario.team_calc:
                scenario.team_calc[team] = {"empty": EmptyRewardCalculator(team)}
        for name, actor in scenario.agents.items():
            if name in names:
                continue
            actor.agent_type = SleepAgent()
            actor.default_actions = (Monitor, {"session": 0, "agent": name}) if name == "Blue" and self.config["scenario"]["defender"] == "monitor" else (Sleep, {})
        targets = self.config["scenario"]["targets"]
        if any(x not in scenario.hosts or x.endswith("_router") or x == "User0" for x in targets):
            raise ValueError("Targets must be non-router enterprise hosts other than the initial foothold User0")
        self.validate_scenario(scenario)
        return scenario
