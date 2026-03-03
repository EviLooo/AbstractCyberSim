# Developer Guide

Extending and modifying `AbstractCyberSim` is easy due to its modular design. Because it utilizes Mesa 3.4+, follow the best practices strictly regarding code composition and Agent isolation.

## Adding a New Feature

When adding logic, you should identify what component your feature logically belongs to:
- If it's a new attacker action (e.g., `SPEARPHISH`), it should be added to `execute_action` inside `CyberAgent`, with corresponding memory rules. It shouldn't be added to the cognition matrix.
- If it's a new topological generation method, add it inside `NetworkEnvironment`.

## Adding a New Cognition Module
To create a new AI or logic algorithm for the attacker (e.g., a Reinforcement Learning attacker):
1. Create a file inside `abms_cyber/agents/cognition/` (e.g., `rl_based.py`).
2. Make a class extending `BaseCognition`.
3. Implement `def decide(self) -> str:` mapping inputs (memory) to action outputs (e.g., `"SCAN:NodeId"`)
4. Switch to your cognition module during initialization in `cyber_model.py`.

## Adding a New Organization Model
If adding a new structural format (e.g., `HierarchicalOrganization`):
1. Replicate `CentralizedOrganization` but add specific `leader` and `sub-leader` behaviors in `step()`.
2. Ensure you modify `step()` to push commands downstream before individual `CyberAgent` processes run.
3. Call the organization in the `__init__` constructor of `CyberModel` when `org_type="hierarchical"` is selected.

## Safe Code Modifications & Common Pitfalls

- **Do not let Agents read global model state!** Agents should only know what their `AgentMemory` tells them or what their `current_node` exposes. Allowing omniscient attackers breaks the fundamental principles of real-world ABMs.
- **Ensure Network Paths:** If `vulnerability_level` generation is modified, ensure there is an actual path to the target node. Without this, your win condition termination loop might never trigger.
- **Mesa 3.4 Considerations:** The newer standard of Mesa discourages deep inheritance graphs. Prefer Composition using separated modules (like `BaseCognition` and `BaseOrganization`) instead of huge monolithic `CyberAgent` parent classes.
- **Check SolaraViz impact:** Altering metric collection data structure inside `data_collector.py` will break the visualizations bound to Solara. Always double-check how visualizations interact with your new keys.
