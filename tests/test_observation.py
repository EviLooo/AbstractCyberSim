import json
import unittest
from types import SimpleNamespace

from abms_cyber.agents.memory import AgentMemory
from abms_cyber.config.default_config import CyberConfig
from abms_cyber.environment.node import CyberNode
from abms_cyber.environment.observation import build_observation


class ObservationTests(unittest.TestCase):
    def make_subject(self):
        source = CyberNode(
            id="0",
            vulnerability_level=0.4,
            compromised=True,
            neighbors=["1"],
        )
        target = CyberNode(
            id="1",
            vulnerability_level=0.7,
            is_target=True,
            neighbors=["0"],
        )
        memory = AgentMemory()
        memory.known_nodes.update({"0", "1"})
        memory.scanned_nodes.add("0")
        memory.action_history.extend(
            ["SCAN:0", "EXPLOIT:0", "ESCALATE:0", "MOVE:1"]
        )
        agent = SimpleNamespace(
            unique_id=7,
            current_node=source,
            privilege_level=0,
            memory=memory,
        )
        network = SimpleNamespace(nodes={"0": source, "1": target})
        model = SimpleNamespace(
            config=CyberConfig(
                num_nodes=2,
                avg_degree=1,
                observation_history_limit=2,
            ),
            network=network,
            org_type="swarm",
            steps=3,
            detection_level=0.2,
        )
        return agent, model

    def test_observation_is_json_ready_and_bounded(self):
        agent, model = self.make_subject()

        observation = build_observation(agent, model)
        encoded = json.dumps(observation)

        self.assertIn('"agent_id": "7"', encoded)
        self.assertEqual(
            observation["local_memory"]["recent_actions"],
            ["ESCALATE:0", "MOVE:1"],
        )
        self.assertEqual(observation["network"]["visibility"], "full_topology")

    def test_observation_lists_only_currently_valid_targets(self):
        agent, model = self.make_subject()

        observation = build_observation(agent, model)

        self.assertEqual(observation["valid_target_ids"]["MOVE"], ["1"])
        self.assertEqual(observation["valid_target_ids"]["EXPLOIT"], [])
        self.assertEqual(observation["valid_target_ids"]["ESCALATE"], ["0"])


if __name__ == "__main__":
    unittest.main()
