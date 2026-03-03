
"""
Agent Local Memory.
"""

from typing import Set, List, Dict, Any

class AgentMemory:
    def __init__(self):
        self.known_nodes: Set[str] = set()
        self.scanned_nodes: Set[str] = set()
        self.compromised_nodes: Set[str] = set()
        self.action_history: List[str] = []
        
    def record_scan(self, node_id: str):
        self.known_nodes.add(node_id)
        self.scanned_nodes.add(node_id)
        
    def record_compromise(self, node_id: str):
        self.known_nodes.add(node_id)
        self.compromised_nodes.add(node_id)
        
    def record_action(self, action: str):
        self.action_history.append(action)
