import json
import unittest

from abms_cyber.config.default_config import CyberConfig
from abms_cyber.environment.network_graph import NetworkEnvironment


def snapshot(environment):
    edges = sorted(tuple(sorted(edge)) for edge in environment.graph.edges())
    nodes = sorted(
        (
            node.id,
            node.vulnerability_level,
            node.privilege_required,
            node.is_target,
            tuple(sorted(node.neighbors)),
        )
        for node in environment.nodes.values()
    )
    return edges, nodes


class NetworkEnvironmentTests(unittest.TestCase):
    def setUp(self):
        self.config = CyberConfig(
            num_nodes=12,
            avg_degree=2,
            num_agents=2,
            random_seed=123,
        )

    def test_same_seed_produces_same_environment(self):
        first = NetworkEnvironment(self.config)
        second = NetworkEnvironment(self.config)

        self.assertEqual(snapshot(first), snapshot(second))

    def test_graph_invariants(self):
        environment = NetworkEnvironment(self.config)

        self.assertEqual(environment.graph.number_of_edges(), 12)
        self.assertEqual(
            sum(node.is_target for node in environment.nodes.values()),
            1,
        )
        for node in environment.nodes.values():
            for neighbor_id in node.neighbors:
                self.assertIn(node.id, environment.nodes[neighbor_id].neighbors)

    def test_node_data_is_json_ready(self):
        environment = NetworkEnvironment(self.config)

        encoded = json.dumps(
            [node.to_dict() for node in environment.nodes.values()]
        )

        self.assertIn("vulnerability_level", encoded)


if __name__ == "__main__":
    unittest.main()
