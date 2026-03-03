
"""
Node representation in the cyber network.
"""

from dataclasses import dataclass, field
from typing import List

@dataclass
class CyberNode:
    id: str
    vulnerability_level: float = 0.0  # 0.0 to 1.0
    privilege_required: int = 0       # 0=User, 1=Admin
    is_target: bool = False
    compromised: bool = False
    scanned: bool = False
    neighbors: List[str] = field(default_factory=list)
    
    def __hash__(self):
        return hash(self.id)
    
    def __eq__(self, other):
        if not isinstance(other, CyberNode):
            return False
        return self.id == other.id
