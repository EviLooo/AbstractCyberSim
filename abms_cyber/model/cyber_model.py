
"""
Core Cyber Simulation Model.
"""

from mesa import Model
from abms_cyber.config.default_config import CyberConfig
from abms_cyber.environment.network_graph import NetworkEnvironment
from abms_cyber.agents.cyber_agent import CyberAgent
from abms_cyber.metrics.data_collector import get_data_collector
from abms_cyber.organization.centralized import CentralizedOrganization
from abms_cyber.organization.swarm import SwarmOrganization
from abms_cyber.agents.cognition.rule_based import RuleBasedCognition
from abms_cyber.environment.action_resolver import ActionResolver

class CyberModel(Model):
    def __init__(self, config: CyberConfig = CyberConfig(), org_type: str = "swarm"):
        super().__init__()
        self.config = config
        self.random.seed(config.random_seed)
        
        self.network = NetworkEnvironment(config, rng=self.random)
        self.detection_level = 0.0
        self.action_resolver = ActionResolver(self)
        
        # Organization
        self.org_type = org_type
        if org_type == "centralized":
            self.organization = CentralizedOrganization(self)
        else:
            self.organization = SwarmOrganization(self)
            
        self._create_agents()
        
        self.datacollector = get_data_collector(self)
        self.running = True

    def _create_agents(self):
        for i in range(self.config.num_agents):
            start_node = self.network.get_random_start_node()
            agent = CyberAgent(self, start_node)
            
            # Helper to assign cognition (could be factory pattern later)
            # For V0.1 Rule Based:
            agent.cognition = RuleBasedCognition(agent)

    def step(self):
        # Organization step (e.g., Centralized planning)
        if self.organization:
            self.organization.step()
            
        # Agent steps
        self.agents.shuffle_do("step")
        
        # Collect data
        self.datacollector.collect(self)
        
        # Check termination
        self._check_termination()

    def _check_termination(self):
        # Check if target compromised with required privilege
        target_compromised = False
        for node in self.network.nodes.values():
            if node.is_target and node.compromised:
                # Check if any agent has privilege on it? 
                # Or just general if we have privilege?
                # Requirement: "Target node compromised with required privilege"
                # Implies we need an agent on it with priv?
                # For now, let's assume if it's compromised, we won.
                # Actually, requirement says "agent.privilege_level == required"
                target_compromised = True
                break
                
        if target_compromised:
            # Check agent privilege
            # Simplified: any agent has high priv
            any_admin = any(a.privilege_level >= self.config.required_privilege for a in self.agents)
            if any_admin:
                self.running = False
                
        if self.detection_level >= self.config.max_detection_level:
            self.running = False
            
        if self.steps >= self.config.max_steps:
             self.running = False

    def count_compromised(self):
        return sum(1 for n in self.network.nodes.values() if n.compromised)
