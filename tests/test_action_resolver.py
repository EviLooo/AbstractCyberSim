import unittest
from types import SimpleNamespace

from abms_cyber.config.default_config import CyberConfig
from abms_cyber.environment.action_resolver import ActionResolver
from abms_cyber.environment.node import CyberNode


class FixedRandom:
    def __init__(self, *values):
        self.values = list(values)

    def random(self):
        return self.values.pop(0)


class FakeNetwork:
    def __init__(self, *nodes):
        self.nodes = {node.id: node for node in nodes}

    def get_node(self, node_id):
        return self.nodes.get(node_id)


def make_world(random_values=(0.0,), **config_values):
    source = CyberNode(id="0", vulnerability_level=0.5, neighbors=["1"])
    target = CyberNode(id="1", vulnerability_level=0.5, neighbors=["0"])
    config = CyberConfig(num_nodes=2, avg_degree=1, **config_values)
    model = SimpleNamespace(
        config=config,
        network=FakeNetwork(source, target),
        random=FixedRandom(*random_values),
        detection_level=0.0,
    )
    agent = SimpleNamespace(current_node=source, privilege_level=0)
    return model, agent, source, target, ActionResolver(model)


class ActionResolverTests(unittest.TestCase):
    def test_invalid_input_does_not_change_state(self):
        model, agent, source, _, resolver = make_world()

        malformed = resolver.resolve(agent, "not-an-action")
        missing = resolver.resolve(agent, {"action": "SCAN", "target_id": "99"})

        self.assertFalse(malformed.valid)
        self.assertFalse(missing.valid)
        self.assertIs(agent.current_node, source)
        self.assertEqual(model.detection_level, 0.0)

    def test_scan_marks_current_node(self):
        model, agent, source, _, resolver = make_world(scan_detection=0.05)

        result = resolver.resolve(agent, {"action": "scan", "target_id": "0"})

        self.assertTrue(result.valid)
        self.assertTrue(result.success)
        self.assertTrue(source.scanned)
        self.assertAlmostEqual(result.detection_delta, 0.05)
        self.assertEqual(result.state_changes["discovered_neighbors"], ["1"])

    def test_move_requires_compromised_source(self):
        _, agent, source, target, resolver = make_world()

        rejected = resolver.resolve(agent, "MOVE:1")
        source.compromised = True
        accepted = resolver.resolve(agent, "MOVE:1")

        self.assertFalse(rejected.valid)
        self.assertTrue(accepted.success)
        self.assertIs(agent.current_node, target)

    def test_exploit_success_and_failure_are_controlled(self):
        success_model, success_agent, success_node, _, success_resolver = make_world(
            random_values=(0.1,)
        )
        success = success_resolver.resolve(success_agent, "EXPLOIT:0")

        failure_model, failure_agent, failure_node, _, failure_resolver = make_world(
            random_values=(0.9,), exploit_failure_detection=0.2
        )
        failure = failure_resolver.resolve(failure_agent, "EXPLOIT:0")

        self.assertTrue(success.success)
        self.assertTrue(success_node.compromised)
        self.assertFalse(failure.success)
        self.assertFalse(failure_node.compromised)
        self.assertAlmostEqual(failure_model.detection_level, 0.2)
        self.assertEqual(success_model.detection_level, 0.0)

    def test_escalation_uses_configured_probability(self):
        model, agent, source, _, resolver = make_world(
            random_values=(0.4,),
            escalate_success_prob=0.5,
        )
        source.compromised = True

        result = resolver.resolve(agent, "ESCALATE:0")

        self.assertTrue(result.success)
        self.assertEqual(agent.privilege_level, model.config.required_privilege)

    def test_detection_is_clamped_to_maximum(self):
        model, agent, _, _, resolver = make_world(
            random_values=(0.9,),
            exploit_failure_detection=0.4,
        )
        model.detection_level = 0.9

        result = resolver.resolve(agent, "EXPLOIT:0")

        self.assertAlmostEqual(model.detection_level, 1.0)
        self.assertAlmostEqual(result.detection_delta, 0.1)


if __name__ == "__main__":
    unittest.main()
