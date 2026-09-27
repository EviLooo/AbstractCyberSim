
"""
Configuration parameters for the ABMS Cyber Simulation.
"""

from dataclasses import dataclass


@dataclass
class CyberConfig:
    # General
    max_steps: int = 100
    random_seed: int = 42
    
    # Network
    num_nodes: int = 20
    avg_degree: int = 3
    vulnerability_min: float = 0.1
    vulnerability_max: float = 0.9
    admin_node_probability: float = 0.2
    
    # Agents
    num_agents: int = 5
    initial_privilege: int = 0
    
    # Detection
    max_detection_level: float = 1.0
    detection_threshold: float = 0.8
    
    # Probabilities
    escalate_success_prob: float = 0.5
    exploit_failure_detection: float = 0.1
    exploit_success_detection: float = 0.0
    escalate_failure_detection: float = 0.1
    escalate_success_detection: float = 0.0
    scan_detection: float = 0.0

    # Movement and observation
    move_requires_compromised_source: bool = True
    observation_history_limit: int = 5
    
    # Target
    required_privilege: int = 1  # 0=User, 1=Admin

    def __post_init__(self) -> None:
        """Reject invalid settings before a simulation starts."""
        if self.max_steps <= 0:
            raise ValueError("max_steps must be greater than zero")
        if self.num_nodes <= 0:
            raise ValueError("num_nodes must be greater than zero")
        if not 0 <= self.avg_degree < self.num_nodes:
            raise ValueError("avg_degree must be between 0 and num_nodes - 1")
        if self.num_agents <= 0:
            raise ValueError("num_agents must be greater than zero")
        if self.observation_history_limit < 0:
            raise ValueError("observation_history_limit cannot be negative")
        if self.max_detection_level <= 0:
            raise ValueError("max_detection_level must be greater than zero")
        if not 0 <= self.detection_threshold <= self.max_detection_level:
            raise ValueError(
                "detection_threshold must be between 0 and max_detection_level"
            )
        if not 0 <= self.vulnerability_min <= self.vulnerability_max <= 1:
            raise ValueError("vulnerability bounds must satisfy 0 <= min <= max <= 1")

        probabilities = {
            "admin_node_probability": self.admin_node_probability,
            "escalate_success_prob": self.escalate_success_prob,
        }
        for name, value in probabilities.items():
            if not 0 <= value <= 1:
                raise ValueError(f"{name} must be between 0 and 1")

        detection_changes = {
            "exploit_failure_detection": self.exploit_failure_detection,
            "exploit_success_detection": self.exploit_success_detection,
            "escalate_failure_detection": self.escalate_failure_detection,
            "escalate_success_detection": self.escalate_success_detection,
            "scan_detection": self.scan_detection,
        }
        for name, value in detection_changes.items():
            if value < 0:
                raise ValueError(f"{name} cannot be negative")

        if self.initial_privilege not in (0, 1):
            raise ValueError("initial_privilege must be 0 (user) or 1 (admin)")
        if self.required_privilege not in (0, 1):
            raise ValueError("required_privilege must be 0 (user) or 1 (admin)")
