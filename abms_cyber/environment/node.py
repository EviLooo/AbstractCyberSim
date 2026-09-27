
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

    def __post_init__(self) -> None:
        if not 0 <= self.vulnerability_level <= 1:
            raise ValueError("vulnerability_level must be between 0 and 1")
        if self.privilege_required not in (0, 1):
            raise ValueError("privilege_required must be 0 (user) or 1 (admin)")

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-ready representation for observations and logs."""
        return {
            "id": self.id,
            "vulnerability_level": round(self.vulnerability_level, 4),
            "privilege_required": self.privilege_required,
            "is_target": self.is_target,
            "compromised": self.compromised,
            "scanned": self.scanned,
            "neighbors": sorted(self.neighbors, key=_node_sort_key),
        }
    
    def __hash__(self):
        return hash(self.id)
    
    def __eq__(self, other):
        if not isinstance(other, CyberNode):
            return False
        return self.id == other.id


def _node_sort_key(node_id: str) -> tuple[int, int | str]:
    """Sort numeric node ids naturally while supporting future string ids."""
    return (0, int(node_id)) if node_id.isdigit() else (1, node_id)
