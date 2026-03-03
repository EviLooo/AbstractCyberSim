
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
    
    # Agents
    num_agents: int = 5
    initial_privilege: int = 0
    
    # Detection
    max_detection_level: float = 1.0
    detection_threshold: float = 0.8
    
    # Probabilities
    escalate_success_prob: float = 0.5
    
    # Target
    required_privilege: int = 1  # 0=User, 1=Admin
