# ARCHITECTURE DIAGRAM: ABMS Cyber Simulation

This file describes architecture using text diagrams and data flow.

## 1. High-Level Architecture

```text
+---------------------------+
|         main.py           |
| CLI modes: experiment/UI  |
+------------+--------------+
             |
             v
+---------------------------+
|  CyberModel (Mesa Model)  |
|  - global state           |
|  - step orchestration     |
+-----+---------------+-----+
      |               |
      v               v
+-----------+   +------------------+
| Network    |   | Organization     |
| Environment|   | (swarm/central)  |
+-----+------+   +---------+--------+
      |                    |
      v                    v
+-----------------------------------+
|        CyberAgent(s)              |
|  - cognition.decide()             |
|  - execute action                 |
|  - memory update                  |
+----------------+------------------+
                 |
                 v
+-----------------------------------+
|   Metrics (Mesa DataCollector)    |
+----------------+------------------+
                 |
                 v
+-----------------------------------+
| Visualization (Solara + Charts)   |
+-----------------------------------+
```

---

## 2. Runtime Data Flow (One Simulation Step)

```text
CyberModel.step()
   |
   |-- 1) organization.step()
   |
   |-- 2) for each agent (shuffled):
   |       agent.step()
   |          -> cognition.decide() returns "ACTION:TARGET"
   |          -> agent.execute_action()
   |             -> modifies node/model state
   |             -> records memory.action_history
   |
   |-- 3) datacollector.collect(model)
   |
   `-- 4) _check_termination()
           -> sets model.running = False when stop condition met
```

---

## 3. Module Dependency Diagram

```text
main.py
  -> abms_cyber.model.cyber_model
  -> abms_cyber.config.default_config

cyber_model.py
  -> config.default_config.CyberConfig
  -> environment.network_graph.NetworkEnvironment
  -> agents.cyber_agent.CyberAgent
  -> agents.cognition.rule_based.RuleBasedCognition
  -> metrics.data_collector.get_data_collector
  -> organization.centralized.CentralizedOrganization
  -> organization.swarm.SwarmOrganization

cyber_agent.py
  -> mesa.Agent
  -> agents.memory.AgentMemory
  -> environment.node.CyberNode

network_graph.py
  -> networkx
  -> environment.node.CyberNode
  -> config.default_config.CyberConfig

visualization/app.py
  -> model.cyber_model.CyberModel
  -> config.default_config.CyberConfig
  -> visualization.network_view.NetworkView
  -> visualization.charts.MetricsChart
```

---

## 4. Core Components and Responsibilities

## A) `CyberModel` (System Orchestrator)

Responsibilities:
- Owns global state (network, detection, agents, config).
- Owns simulation loop control (`running`).
- Calls organization and agents each step.
- Collects metrics.
- Enforces stop conditions.

Key state:
- `network`
- `detection_level`
- `organization`
- `agents`
- `datacollector`

---

## B) `NetworkEnvironment` (World State)

Responsibilities:
- Build random graph topology.
- Create domain nodes (`CyberNode`).
- Mark one node as target.
- Provide node lookup and start node selection.

Key state:
- `graph` (NetworkX graph)
- `nodes` dict (`str node_id -> CyberNode`)

---

## C) `CyberAgent` (Actor)

Responsibilities:
- Ask cognition module what to do.
- Execute action against model/world.
- Update its own memory.

Key state:
- `current_node`
- `privilege_level`
- `memory`
- `cognition`

---

## D) Cognition Layer (Decision Policy)

`BaseCognition`:
- Interface contract for decision modules.

`RuleBasedCognition`:
- Priority rules for scan/exploit/escalate/move.

Role in architecture:
- Separates "decision policy" from "action execution".

---

## E) Organization Layer (Coordination Policy)

`SwarmOrganization`:
- Currently passive; agents act independently.

`CentralizedOrganization`:
- Placeholder for leader-subordinate control.

Role in architecture:
- Intended to control group-level behavior before individual agent steps.

---

## F) Metrics + Visualization

Metrics:
- `DataCollector` records model/agent values each step.

Visualization:
- Solara page controls stepping/reset.
- Matplotlib view shows network and agent positions.
- Plotly chart shows metric trends.

---

## 5. State Model Diagram

```text
CyberModel
  config: CyberConfig
  network: NetworkEnvironment
  detection_level: float
  org_type: str
  organization: BaseOrganization
  agents: AgentSet[CyberAgent]
  datacollector: DataCollector
  running: bool

NetworkEnvironment
  graph: nx.Graph
  nodes: Dict[str, CyberNode]

CyberNode
  id: str
  vulnerability_level: float
  privilege_required: int
  is_target: bool
  compromised: bool
  scanned: bool
  neighbors: List[str]

CyberAgent
  current_node: CyberNode
  privilege_level: int
  memory: AgentMemory
  cognition: BaseCognition

AgentMemory
  known_nodes: Set[str]
  scanned_nodes: Set[str]
  compromised_nodes: Set[str]
  action_history: List[str]
```

---

## 6. Action Processing Diagram

Action string format:

```text
ACTION:TARGET_ID
```

Routing in `CyberAgent.execute_action()`:

```text
MOVE:x      -> move(x)
SCAN:x      -> scan(x)
EXPLOIT:x   -> exploit(x)
ESCALATE:x  -> escalate(x)
```

State impact summary:
- `MOVE`: changes `agent.current_node`.
- `SCAN`: sets `node.scanned=True`, updates memory knowledge.
- `EXPLOIT`: may set `node.compromised=True`; failure raises detection.
- `ESCALATE`: may increase `agent.privilege_level`.

---

## 7. Termination Logic Diagram

```text
Check 1: target compromised?
  -> yes: any agent privilege >= required?
       -> yes: stop

Check 2: detection_level >= max_detection_level?
  -> yes: stop

Check 3: steps >= max_steps?
  -> yes: stop
```

Stop signal:
- `model.running = False`

---

## 8. Visualization Data Flow

```text
User clicks Step (UI)
   -> step_model()
      -> wrapper.model.step()
      -> step_counter += 1 (reactive trigger)
         -> Page() rerender
            -> NetworkView(model) refresh
            -> DataFrame from datacollector
            -> MetricsChart(df) refresh
```

---

## 9. Current Architectural Gaps

1. `abms_cyber/run.py` is placeholder.
2. `CentralizedOrganization` coordination behavior is not implemented.
3. Some config values are defined but not fully used (`detection_threshold`, `escalate_success_prob`).
4. Success criteria are simplified and can be made more realistic.

---

## 10. Recommended Next Architecture Improvements

1. Implement centralized task assignment protocol.
2. Add explicit action objects instead of string parsing.
3. Use config values consistently in agent logic.
4. Add event log subsystem for explainability/debugging.
5. Add unit tests around action effects and stop conditions.
