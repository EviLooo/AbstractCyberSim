# Glossary of Important Terms

This domain-specific glossary aims to help newcomers understand the terminology used in AbstractCyberSim documentation and code:

* **ABM (Agent-Based Modeling)**: A computational model simulation mimicking the actions and interactions of autonomous agents assessing their effects on the system as a whole.
* **Mesa**: An open-source Python framework for developing Agent-Based Models.
* **Agent / CyberAgent**: The representation of the software acting on behalf of an attacker or attacking force attempting to achieve the compromise goal.
* **Node (CyberNode)**: Analogous to a computer, server, router, or endpoint on a network.
* **Target Node**: The singular "goal" computer that the agents aim to locate and exploit. Attacking this successfully fulfills their objective.
* **Cognition**: The isolated internal reasoning loop of the agent (`decide()`), simulating how a human attacker would process situations probabilistically or via rules.
* **Privilege Level**: Represents an agent's permissions on the nodes they reside in (e.g., `0=User`, `1=Admin`). Escaping detection requires higher privilege levels on target servers.
* **Vulnerability Level**: A scalar heuristic bounded `0.0 to 1.0` indicating how likely a node is to successfully succumb to an `EXPLOIT` command.
* **Detection Level**: The aggregate alarm mechanism in the environment. Exceeding `max_detection_level` mimics blue-team responses intervening and ending the attack.
* **Centralized Organization**: An organization behavior wherein attacker agents report to a central node/leader that globally optimizes routing decisions and task assignments.
* **Swarm Organization**: An unstructured methodology where independent agents follow their cognition randomly without an orchestrating leader aligning their strategies.
* **Solara**: The pure Python visualization framework used by Mesa 3.4 for generating modern, interactive dashboard frontends without deep Javascript integration.
