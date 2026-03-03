# ABMS_CYBER Beginner Documentation

This document explains the `abms_cyber` package for a beginner programmer with no Mesa background.

## 1. What This Project Is

`abms_cyber` is an **agent-based cyber attack simulation**.

- A network is generated with many nodes (computers/systems).
- Attack agents move through the network.
- Agents scan, exploit vulnerabilities, and escalate privileges.
- The model tracks detection risk, compromised systems, and stop conditions.

The package is organized into modules for:
- agents
- environment
- cognition (decision logic)
- organization style (swarm/centralized)
- metrics
- visualization
- model orchestration

## 2. Quick Mesa Concepts (Beginner Level)

Mesa is a Python framework for agent-based simulations.

- `Model`: the whole simulation world and its global state.
- `Agent`: an individual actor that does something each step.
- `step()`: one simulation tick; both model and agents have one.
- `DataCollector`: records values over time (for charts/analysis).

In this code:
- `CyberModel` is the Mesa model.
- `CyberAgent` is the Mesa agent.

## 3. Package Structure

```text
abms_cyber/
  __init__.py
  run.py
  agents/
    cyber_agent.py
    memory.py
    cognition/
      base_cognition.py
      rule_based.py
  config/
    default_config.py
  environment/
    node.py
    network_graph.py
  metrics/
    data_collector.py
  model/
    cyber_model.py
  organization/
    base_org.py
    centralized.py
    swarm.py
  visualization/
    app.py
    charts.py
    network_view.py
    portrayal.py
```

---

## 4. File-by-File Documentation

## `abms_cyber/__init__.py`

Purpose:
- Marks `abms_cyber` as a Python package.

What it does:
- Currently empty. No runtime logic.

---

## `abms_cyber/run.py`

Purpose:
- Intended command-line entry point for package-level execution.

What it does now:
- Adds parent folder to Python path.
- Imports are prepared in `if __name__ == "__main__":` block.
- Contains `pass`, so no actual run behavior yet.

Beginner note:
- This is a placeholder file. Real simulation execution is currently done via root `main.py`.

---

## `abms_cyber/agents/cyber_agent.py`

Purpose:
- Defines the attacker agent behavior.

Class: `CyberAgent(Agent)`

### `__init__(self, model, start_node)`
Sets initial agent state:
- `self.current_node`: where agent starts.
- `self.privilege_level`: starts at 0.
- `self.memory`: local memory object (`AgentMemory`).
- `self.cognition`: decision module (assigned later).
- Adds start node ID to known nodes memory.

### `step(self)`
- Called once per simulation tick for this agent.
- If cognition exists, asks cognition for an action string.
- Runs `execute_action(action)`.

### `execute_action(self, action_str)`
- Parses action string format: `ACTION:TARGET_ID`.
- Routes to:
  - `move(target_id)`
  - `scan(target_id)`
  - `exploit(target_id)`
  - `escalate(target_id)`
- Records action in memory (`action_history`).

### `move(self, target_id)`
- Checks if target is a neighbor of current node.
- If valid, updates `self.current_node` to that node.
- Adds target to known nodes.

### `scan(self, target_id)`
- Marks target node as scanned.
- Records scan in memory.
- Discovers target node neighbors and adds them to memory.

### `exploit(self, target_id)`
- Gets target node.
- Attempts exploit with probability = `node.vulnerability_level`.
- On success: node becomes compromised.
- On failure: increases model detection level (`+0.1`).

### `escalate(self, target_id)`
- Only works if target is current node and node is compromised.
- 50% chance to set `privilege_level = 1`.

Beginner note:
- Agent decision and action execution are separated.
- Cognition decides what to do; agent methods do the actual state changes.

---

## `abms_cyber/agents/memory.py`

Purpose:
- Stores each agent's local knowledge/history.

Class: `AgentMemory`

Fields:
- `known_nodes`: set of discovered node IDs.
- `scanned_nodes`: scanned node IDs.
- `compromised_nodes`: successfully exploited node IDs.
- `action_history`: chronological list of action strings.

Methods:
- `record_scan(node_id)`
- `record_compromise(node_id)`
- `record_action(action)`

Beginner note:
- This is agent-local memory, not global model truth.

---

## `abms_cyber/agents/cognition/base_cognition.py`

Purpose:
- Abstract interface for decision modules.

Class: `BaseCognition(ABC)`

### `__init__(self, agent)`
- Saves a reference to the owning agent.

### `decide(self) -> str` (abstract)
- Must return an action string like `SCAN:3`.

Beginner note:
- You can create multiple cognition strategies by subclassing this.

---

## `abms_cyber/agents/cognition/rule_based.py`

Purpose:
- Concrete rule-driven decision strategy.

Class: `RuleBasedCognition(BaseCognition)`

### `decide(self) -> str`
Decision order used:
1. If current node is target and not compromised -> `EXPLOIT:current`
2. If current node is not scanned -> `SCAN:current`
3. If current node is not compromised -> `EXPLOIT:current`
4. If agent privilege below required -> `ESCALATE:current`
5. Else move to random neighbor -> `MOVE:neighbor`
6. Else fallback -> `WAIT:None`

Beginner note:
- Rule ordering matters. Earlier conditions override later ones.

---

## `abms_cyber/config/default_config.py`

Purpose:
- Central configuration for simulation parameters.

Dataclass: `CyberConfig`

Fields:
- `max_steps`: max simulation ticks.
- `random_seed`: seed for reproducibility.
- `num_nodes`, `avg_degree`: network shape.
- `num_agents`: number of attacker agents.
- `initial_privilege`: starting privilege (currently not fully wired into agent init).
- `max_detection_level`: hard stop threshold.
- `detection_threshold`: present, but not used in termination right now.
- `escalate_success_prob`: present, but agent code currently hardcodes 0.5.
- `required_privilege`: privilege needed for mission success.

Beginner note:
- Some config fields are placeholders for future cleanup/integration.

---

## `abms_cyber/environment/node.py`

Purpose:
- Data model for one network node.

Dataclass: `CyberNode`

Fields:
- `id`: node identifier string.
- `vulnerability_level`: exploit success probability driver.
- `privilege_required`: 0 user / 1 admin needed.
- `is_target`: whether this is the mission target.
- `compromised`: compromised status.
- `scanned`: scanned status.
- `neighbors`: list of adjacent node IDs.

Special methods:
- `__hash__`, `__eq__`: nodes compare/hash by `id`.

---

## `abms_cyber/environment/network_graph.py`

Purpose:
- Builds and manages the simulated network environment.

Class: `NetworkEnvironment`

### `__init__(self, config)`
- Creates random graph with NetworkX: `gnm_random_graph`.
- Initializes `self.nodes` dict of `CyberNode` objects.
- Calls `_initialize_nodes()`.

### `_initialize_nodes(self)`
Steps:
- For each graph node:
  - Assign random vulnerability in `[0.1, 0.9]`.
  - Assign admin requirement with 20% chance.
  - Create `CyberNode`.
- For each graph edge:
  - Fill node neighbor lists (undirected).
- Pick one random target node:
  - Prefer admin-required nodes; fallback to any node.

### `get_node(self, node_id)`
- Returns `CyberNode` or `None`.

### `get_random_start_node(self)`
- Picks non-target, low-privilege node when possible.
- Falls back to any random node.

Beginner note:
- This class is the simulation world map.

---

## `abms_cyber/metrics/data_collector.py`

Purpose:
- Defines what simulation data to record each step.

Function: `get_data_collector(model)`

Returns Mesa `DataCollector` with:

Model reporters:
- `Detection_Level`
- `Compromised_Nodes`
- `Steps`

Agent reporters:
- `Action` (last action or `None`)
- `Privilege`

Beginner note:
- Reporter values appear in tables/charts after stepping model.

---

## `abms_cyber/model/cyber_model.py`

Purpose:
- Main simulation controller.

Class: `CyberModel(Model)`

### `__init__(self, config=CyberConfig(), org_type="swarm")`
Initializes:
- Config and random seed.
- Network environment.
- Detection level.
- Organization module (`CentralizedOrganization` or `SwarmOrganization`).
- Agents.
- Data collector.
- `running=True` flag.

### `_create_agents(self)`
- Creates `num_agents` `CyberAgent` objects.
- Assigns random start nodes.
- Assigns `RuleBasedCognition`.

### `step(self)`
Order of operations each tick:
1. organization step
2. agent steps (`self.agents.shuffle_do("step")`)
3. data collection
4. termination check

### `_check_termination(self)`
Stops simulation if any condition true:
- target compromised AND some agent has required privilege
- detection level >= max detection level
- step count >= max steps

### `count_compromised(self)`
- Counts compromised nodes in environment.

Beginner notes:
- `self.running` is the key loop condition.
- Success logic is simplified and can be refined (e.g., tie agent privilege to target location).

---

## `abms_cyber/organization/base_org.py`

Purpose:
- Interface for organization coordination strategies.

Class: `BaseOrganization(ABC)`

### `__init__(self, model)`
- Stores model reference.

### `step(self)` (abstract)
- Called each model step before agents act.

---

## `abms_cyber/organization/swarm.py`

Purpose:
- Decentralized mode.

Class: `SwarmOrganization(BaseOrganization)`

### `step(self)`
- Currently `pass`.
- Practical meaning: agents decide independently in their own `step()`.

---

## `abms_cyber/organization/centralized.py`

Purpose:
- Placeholder for centralized/leader strategy.

Class: `CentralizedOrganization(BaseOrganization)`

### `__init__(self, model)`
- Initializes `leader=None`.

### `step(self)`
- Attempts to select first agent as leader.
- Contains design comments, but no implemented coordination behavior yet (`pass`).

Beginner note:
- This file is scaffolding for future work.

---

## `abms_cyber/visualization/app.py`

Purpose:
- Solara web UI entrypoint.

Important globals:
- `config = CyberConfig(num_agents=5)`
- `wrapper = ModelWrapper()` holds persistent `CyberModel`.
- `step_counter = solara.reactive(0)` triggers rerenders.

Class: `ModelWrapper`
- Keeps `model` instance and `running` flag.

Component: `Page()`
- Main UI layout:
  - title + description
  - `Step` button (advance one tick)
  - `Reset` button
  - status metrics text
  - `NetworkView(model)`
  - `MetricsChart(df)`

Functions:
- `step_model()`
  - Calls model step if running.
  - Increments reactive counter.
- `reset_model()`
  - Recreates model instance.
  - Resets step counter.

Component: `App()`
- Solara entrypoint that renders `Page()`.

Beginner note:
- Solara components rerender when reactive state changes.

---

## `abms_cyber/visualization/network_view.py`

Purpose:
- Renders network state visually with Matplotlib.

Component: `NetworkView(model)`

Process:
- Builds figure/axes.
- Reads network graph `G`.
- Computes stable positions with `nx.spring_layout(seed=42)`.
- Draws nodes and edges.
- Colors/sizes nodes using portrayal helpers.
- Overlays agents as triangle markers at current node positions.
- Hides axes.

Beginner note:
- Node IDs in NetworkX are ints; code converts to strings for `CyberNode` lookup.

---

## `abms_cyber/visualization/portrayal.py`

Purpose:
- Visual styling rules for nodes/agents.

Functions:
- `get_node_color(node)`
  - red if compromised
  - yellow if scanned
  - green otherwise
- `get_node_size(node)`
  - larger for target node
- `get_agent_color(agent)`
  - blue for swarm
  - cyan otherwise
- `get_agent_size(agent)`
  - base size + bonus for privilege

---

## `abms_cyber/visualization/charts.py`

Purpose:
- Live metrics line chart.

Component: `MetricsChart(df)`
- If dataframe empty -> show waiting text.
- Else plotly line chart:
  - x-axis: `Steps`
  - y-axis: `Detection_Level`, `Compromised_Nodes`

Beginner note:
- Chart depends on `DataCollector` output from model steps.

---

## 5. How Everything Connects (Execution Flow)

Typical run path (from root `main.py` experiment mode):

1. Build `CyberModel`.
2. `CyberModel` builds `NetworkEnvironment`.
3. Model creates agents and assigns `RuleBasedCognition`.
4. Loop while `model.running`:
   - call `model.step()`
   - organization step runs
   - agents decide + act
   - metrics collected
   - termination evaluated
5. Print end-of-trial stats.

Visualization mode:
- Solara app repeatedly calls `step_model()` on button click.
- UI updates network and charts from current model state.

## 6. Current Gaps / TODOs in This Codebase

- `abms_cyber/run.py` is placeholder, not full CLI runner.
- `CentralizedOrganization.step()` is mostly unimplemented.
- `detection_threshold` and `escalate_success_prob` config values are not fully wired into runtime logic.
- Success condition is simplified (target compromise + any admin agent).

## 7. Beginner-Friendly Tips for Extending the Project

Good first improvements:

1. Wire config into agent behavior:
- Use `config.escalate_success_prob` in `CyberAgent.escalate`.

2. Implement centralized behavior:
- Make leader assign concrete actions to other agents.

3. Improve termination realism:
- Require privileged agent to be on target node.

4. Add more cognition modules:
- Create `agents/cognition/probabilistic.py` implementing `BaseCognition`.

5. Add tests:
- Unit tests for `exploit`, `move`, `scan`, and termination logic.

## 8. Quick Reference Table

| Area | Main File | Responsibility |
|---|---|---|
| Agent logic | `agents/cyber_agent.py` | Executes actions and changes world state |
| Agent memory | `agents/memory.py` | Stores local knowledge/history |
| Decision logic | `agents/cognition/rule_based.py` | Picks next action |
| Config | `config/default_config.py` | Tunable simulation parameters |
| Network world | `environment/network_graph.py` | Build graph + nodes + target |
| Node schema | `environment/node.py` | Node state fields |
| Model core | `model/cyber_model.py` | Step loop, orchestration, termination |
| Org strategy | `organization/*.py` | Swarm/centralized coordination patterns |
| Metrics | `metrics/data_collector.py` | Data collection hooks |
| UI app | `visualization/app.py` | Solara page and controls |
| UI network | `visualization/network_view.py` | Topology rendering |
| UI styling | `visualization/portrayal.py` | Node/agent visual mapping |
| UI charts | `visualization/charts.py` | Plotly metrics chart |

---

If you want, next I can also create:
- `BEGINNER_WALKTHROUGH.md` (hands-on tutorial with "run this, then inspect this")
- `ARCHITECTURE_DIAGRAM.md` (text diagram + data flow)
- a cleaned `README.md` that links all docs.
