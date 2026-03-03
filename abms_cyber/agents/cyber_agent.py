
"""
Base Abstract Cyber Agent.
"""

from mesa import Agent
from abms_cyber.agents.memory import AgentMemory
from abms_cyber.environment.node import CyberNode

class CyberAgent(Agent):
    def __init__(self, model, start_node: CyberNode):
        super().__init__(model)
        self.current_node = start_node
        self.privilege_level = 0
        self.memory = AgentMemory()
        self.cognition = None  # To be set by organization or config
        
        # Initial memory of start node
        self.memory.known_nodes.add(start_node.id)

    def step(self):
        if self.cognition:
            action = self.cognition.decide()
            self.execute_action(action)

    def execute_action(self, action_str: str):
        # Format: ACTION:TARGET_ID
        parts = action_str.split(":")
        action_type = parts[0]
        target_id = parts[1] if len(parts) > 1 else None
        
        # This logic will need an ActionResolver in the environment
        # For now, implemented simply
        if action_type == "MOVE":
            self.move(target_id)
        elif action_type == "SCAN":
            self.scan(target_id)
        elif action_type == "EXPLOIT":
            self.exploit(target_id)
        elif action_type == "ESCALATE":
            self.escalate(target_id)
            
        self.memory.record_action(action_str)

    def move(self, target_id):
        # Check connectivity
        if target_id in self.current_node.neighbors:
             node = self.model.network.get_node(target_id)
             if node: # and node.compromised (rule says move to compromised?)
                 # For V0.1 simplistic move, check if neighbor
                 self.current_node = node
                 self.memory.known_nodes.add(target_id)

    def scan(self, target_id):
        node = self.model.network.get_node(target_id)
        if node:
             node.scanned = True
             self.memory.record_scan(target_id)
             # Discover neighbors
             for n_id in node.neighbors:
                 self.memory.known_nodes.add(n_id)

    def exploit(self, target_id):
        node = self.model.network.get_node(target_id)
        if node:
            # Deterministic for V0.1 basic skeleton, probabilistic later
            import random
            if random.random() < node.vulnerability_level:
                node.compromised = True
                self.memory.record_compromise(target_id)
            else:
                 self.model.detection_level += 0.1

    def escalate(self, target_id):
        # Increase privilege on current node
        if self.current_node.id == target_id and self.current_node.compromised:
             if self.model.random.random() < 0.5:
                 self.privilege_level = 1
