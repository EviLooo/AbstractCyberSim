
"""
Network Graph management.
"""

import networkx as nx
import random
from typing import Dict, List, Optional
from abms_cyber.environment.node import CyberNode
from abms_cyber.config.default_config import CyberConfig

class NetworkEnvironment:
    def __init__(self, config: CyberConfig):
        self.config = config
        self.graph = nx.gnm_random_graph(config.num_nodes, config.num_nodes * config.avg_degree)
        self.nodes: Dict[str, CyberNode] = {}
        self._initialize_nodes()
        
    def _initialize_nodes(self):
        # Convert nx nodes to CyberNodes
        for i in self.graph.nodes():
            node_id = str(i)
            # Vulnerability: random float between 0.1 and 0.9
            vuln = random.uniform(0.1, 0.9)
            # Privilege: 20% chance of needing Admin
            priv = 1 if random.random() < 0.2 else 0
            
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
        
        target = random.choice(potential_targets)
        target.is_target = True
        
    def get_node(self, node_id: str) -> Optional[CyberNode]:
        return self.nodes.get(node_id)
        
    def get_random_start_node(self) -> CyberNode:
        # Start at a non-target, low privilege node
        candidates = [n for n in self.nodes.values() if not n.is_target and n.privilege_required == 0]
        if not candidates:
            return random.choice(list(self.nodes.values()))
        return random.choice(candidates)
