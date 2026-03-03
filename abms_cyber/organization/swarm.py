
"""
Swarm Organization.
No leader, independent decisions.
"""

from abms_cyber.organization.base_org import BaseOrganization

class SwarmOrganization(BaseOrganization):
    def step(self):
        # In Swarm, agents decide for themselves in their own step() method.
        # This class might just be a placebo or handle global swarm parameters.
        pass
