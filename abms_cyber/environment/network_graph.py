
"""
Network Graph management.
"""

import networkx as nx
import random
from typing import Dict, Optional
from abms_cyber.environment.node import CyberNode
from abms_cyber.config.default_config import CyberConfig


class NetworkEnvironment:
    def __init__(
        self,
        config: CyberConfig,
        rng: Optional[random.Random] = None,
    ) -> None:
        self.config = config
        self.random = rng or random.Random(config.random_seed)
        edge_count = round(config.num_nodes * config.avg_degree / 2)
        self.graph = nx.gnm_random_graph(
            config.num_nodes,
            edge_count,
            seed=self.random,
        )
        self.nodes: Dict[str, CyberNode] = {}
        self._initialize_nodes()
        
    def _initialize_nodes(self) -> None:
        # Convert nx nodes to CyberNodes
        for i in self.graph.nodes():
            node_id = str(i)
            vuln = self.random.uniform(
                self.config.vulnerability_min,
                self.config.vulnerability_max,
            )
            priv = (
                1
                if self.random.random() < self.config.admin_node_probability
                else 0
            )
            
            self.nodes[node_id] = CyberNode(
                id=node_id,
                vulnerability_level=vuln,
                privilege_required=priv
            )
            
        # Set neighbors
        for u, v in self.graph.edges():
            u_id, v_id = str(u), str(v)
            if v_id not in self.nodes[u_id].neighbors:
                self.nodes[u_id].neighbors.append(v_id)
            if u_id not in self.nodes[v_id].neighbors:
                self.nodes[v_id].neighbors.append(u_id)
                
        # Pick one random target (prefer Admin)
        potential_targets = [n for n in self.nodes.values() if n.privilege_required == 1]
        if not potential_targets:
            potential_targets = list(self.nodes.values())
        
        target = self.random.choice(potential_targets)
        target.is_target = True
        
    def get_node(self, node_id: str) -> Optional[CyberNode]:
        return self.nodes.get(node_id)
        
    def get_random_start_node(self) -> CyberNode:
        # Start at a non-target, low privilege node
        candidates = [n for n in self.nodes.values() if not n.is_target and n.privilege_required == 0]
        if not candidates:
            return self.random.choice(list(self.nodes.values()))
        return self.random.choice(candidates)
