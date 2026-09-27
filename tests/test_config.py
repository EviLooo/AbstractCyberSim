import unittest

from abms_cyber.config.default_config import CyberConfig


class CyberConfigTests(unittest.TestCase):
    def test_default_config_is_valid(self):
        config = CyberConfig()

        self.assertEqual(config.num_nodes, 20)
        self.assertEqual(config.observation_history_limit, 5)

    def test_invalid_values_are_rejected(self):
        invalid_configs = [
            {"max_steps": 0},
            {"num_nodes": 0},
            {"num_nodes": 3, "avg_degree": 3},
            {"num_agents": 0},
            {"escalate_success_prob": 1.1},
            {"vulnerability_min": 0.8, "vulnerability_max": 0.2},
            {"exploit_failure_detection": -0.1},
            {"observation_history_limit": -1},
        ]

        for values in invalid_configs:
            with self.subTest(values=values), self.assertRaises(ValueError):
                CyberConfig(**values)


if __name__ == "__main__":
    unittest.main()
