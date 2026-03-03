
"""
Base Cognition Interface.
"""

from abc import ABC, abstractmethod
from typing import Any

class BaseCognition(ABC):
    def __init__(self, agent):
        self.agent = agent
        
    @abstractmethod
    def decide(self) -> str:
        """
        Returns an action string (e.g., "SCAN:node_1", "MOVE:node_2")
        """
        pass
