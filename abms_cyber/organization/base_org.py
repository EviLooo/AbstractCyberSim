
"""
Base Organization Interface.
"""

from abc import ABC, abstractmethod

class BaseOrganization(ABC):
    def __init__(self, model):
        self.model = model
        
    @abstractmethod
    def step(self):
        """
        Organization-level step. 
        For centralized, this might involve the leader assigning tasks.
        For swarm, this might be a pass-through or empty.
        """
        pass
