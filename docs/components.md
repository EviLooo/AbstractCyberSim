# Component Breakdown

The `abms_cyber` repository is divided into specific sub-packages based on separation of concerns.

## `Root Directory`
**What it does:** Contains the main entry point for running experiments or visualizations.
**Key Files:** `main.py`
**Important things to know:** `main.py` uses `argparse` to allow executing the simulation in either `experiment` mode (headless) or `visualize` mode (interactive UI with Solara).

## `abms_cyber/model/`
**What it does:** Contains the entry point for the Mesa simulation logic.
**Key Files:** `cyber_model.py`
**Important things to know:** `CyberModel` acts as the root class. All configuration parameters (`config.py`) are passed here. It orchestrates the order of operations by progressing the `BaseOrganization`, shuffling the `agents`, and collecting data at the end of every step.

## `abms_cyber/agents/`
**What it does:** Represents the attacker entities. Includes mechanisms for their memory and reasoning logic (cognition).
**Key Files:** `cyber_agent.py`, `memory.py`, `cognition/rule_based.py`
**Important things to know:** 
- `CyberAgent` is the "physical body" within the network. It handles the specific implementation of actions (`MOVE`, `SCAN`, `EXPLOIT`, `ESCALATE`).
- `AgentMemory` is an isolated container holding what the agent *thinks* the network looks like.
- `cognition/` is completely decoupled. To change how an agent acts, you swap its cognition module, not the `CyberAgent` class.

## `abms_cyber/environment/`
**What it does:** Emulates the simulated target network topology.
**Key Files:** `network_graph.py`, `node.py`
**Important things to know:** The environment uses `networkx` to generate a backend graph. However, agents directly engage with `CyberNode` python objects. Each `CyberNode` encapsulates state (vulnerability level, compromise state, etc.).

## `abms_cyber/organization/`
**What it does:** Dictates the high-level coordination strategies of the agents.
**Key Files:** `base_org.py`, `centralized.py`, `swarm.py`
**Important things to know:** The organization `step()` is called *before* the agents' `step()`. In a `Swarm` setup, this module essentially does nothing. In a `Centralized` setup, it allows a leader to preemptively coordinate subordinates before they run their individual steps.

## `abms_cyber/metrics/` & `abms_cyber/visualization/`
**What it does:** Handles the collection of statistics during a run and rendering the state to the user.
**Key Files:** `data_collector.py`, visualization tools (Solara)
**Important things to know:** Uses Mesa's native `DataCollector`. Metrics gathered here are what the visualizer displays on the main dashboard.
