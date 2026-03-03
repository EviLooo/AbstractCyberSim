# Execution Flow / Lifecycle

A single run of AbstractCyberSim follows a classic initialization, execution, and termination phases.

## 1. Bootstrapping (`main.py`)
Execution always begins via `main.py`. The user provides arguments (e.g., `--mode`, `--org`, `--trials`) to dictate the flow.
- If `--mode experiment`: `main.py` directly instantiates `CyberModel` in a headless loop, fast-forwarding until termination.
- If `--mode visualize`: `main.py` spins up a `subprocess` running Solara to serve the interactive web components.

## 2. Initialization (`__init__`)
When `CyberModel(config, org_type)` is instantiated:
1. The `NetworkEnvironment` generates an interconnected graph of `CyberNodes` via NetworkX. One node is flagged `is_target=True`.
2. Based on the selected `org_type` ("swarm" vs "centralized"), the overarching organizational logic is initialized.
3. The model iterates and spawns `CyberAgent` objects up to `config.num_agents`, placing them on non-target starting nodes with weak privileges. Each agent is infused with a specific Cognition matrix (`RuleBasedCognition` by default).

## 2. Main Loop (`step()`)
The main loop runs on a standard `while self.running:` configuration. Every `step()`:
1. **Organization Execution:** If `Centralized`, the leader performs high-level checks across subordinates.
2. **Agent Execution:** The `Mesa` scheduler shuffles the order of agents to ensure fairness and loops through them calling `step()`.
3. **Data Collection:** Once all agents have taken their turn, the `DataCollector` snapshots the state of the network (e.g., number of compromised nodes) and agents (e.g., detection levels).

## 3. Termination Checks (`_check_termination()`)
At the end of every step, the `CyberModel` determines if the simulation should end:
**Win Condition (Attacker):**
The target node (`is_target`) has its `compromised` flag set to `True`, AND an agent possesses a privilege level `privilege_level` greater than or equal to the required `required_privilege` defined in the config.
**Loss Condition (Attacker Detected/Timeout):**
The simulation's global `detection_level` exceeds the `max_detection_level`. Alternatively, if the total running clock ticks exceed `max_steps`.

Once terminated, the final metrics can be reviewed or rendered in Solara visualizations.
