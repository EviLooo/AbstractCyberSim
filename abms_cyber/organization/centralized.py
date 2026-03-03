
"""
Centralized Organization.
Leader agent decides for subordinates.
"""

from abms_cyber.organization.base_org import BaseOrganization

class CentralizedOrganization(BaseOrganization):
    def __init__(self, model):
        super().__init__(model)
        # Identify leader (e.g., first agent)
        self.leader = None
        
    def step(self):
        if not self.leader:
            agents = self.model.schedule.agents
            if agents:
                self.leader = agents[0]
                
        # Logic: Leader gathers info from all agents, then assigns tasks.
        # For V0.1, we can simplify this or make it explicit.
        # If the requirement says "Sub-agents do not decide independently",
        # then we might override their cognition or have the leader call their execute_action directly.
        
        # Implementation Detail:
        # In Mesa, agents usually have a step().
        # If Org is centralized, Agent.step() might delegate to Org, or Org.step() calls Agent.execute_action().
        pass
