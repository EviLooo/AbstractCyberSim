
"""
Rule-Based Cognition Module.
Deterministic decision making.
"""

import random
from abms_cyber.agents.cognition.base_cognition import BaseCognition

class RuleBasedCognition(BaseCognition):
    def decide(self) -> str:
        agent = self.agent
        current_node = agent.current_node
        memory = agent.memory
        
        # 1. If target reachable and exploitable → attempt exploit
        # (Simplified: if current node is target and not compromised)
        if current_node.is_target and not current_node.compromised:
            return f"EXPLOIT:{current_node.id}"
            
        # 2. If current node not scanned → SCAN
        if not current_node.scanned:
            return f"SCAN:{current_node.id}"
            
        # 3. If exploitable (and not compromised) → EXPLOIT
        # (Assuming 'exploitable' means we know it's there and it's not compromised yet)
        if not current_node.compromised:
            return f"EXPLOIT:{current_node.id}"
            
        # 4. If privilege low → ESCALATE
        # (Assuming we need privilege for something, or just general escalation)
        if agent.privilege_level < agent.model.config.required_privilege:
             return f"ESCALATE:{current_node.id}"
             
        # 5. Else MOVE randomly
        # Move to a neighbor
        if current_node.neighbors:
            target = random.choice(current_node.neighbors)
            return f"MOVE:{target}"
            
        return "WAIT:None"
