# AbstractCyberSim Documentation

Welcome to the **AbstractCyberSim** documentation! This interactive website serves as a guide for understanding the architecture, execution flow, and extension points of the simulation.

## High-Level Overview

**What the project does:**
AbstractCyberSim is an Agent-Based Modeling (ABM) simulation built using the [Mesa framework (Version 3.4+)](https://mesa.readthedocs.io/en/latest/). It simulates a cyber-security scenario where autonomous attacker agents interact with a computer network environment to find vulnerabilities, escalate privileges, and compromise designated target nodes.

**The main purpose and goals:**
The primary goal is to study the behavior of both structured (e.g., Centralized) and unstructured (e.g., Swarm) groups of cyber attackers within various network topologies. By simulating the attackers' cognition and the network's vulnerabilities, researchers can evaluate the effectiveness of different defensive and offensive strategies.

**The core features:**
- **Network Environment:** A randomly generated network graph where each node possesses different vulnerability levels and required privileges.
- **Cyber Agents:** Attackers capable of maneuvering through the network to `SCAN`, `MOVE`, `EXPLOIT`, and `ESCALATE`.
- **Cognition Models:** Modular logic dictating agent behavior (e.g., Rule-based logic).
- **Organizations:** Structural management defining how agents coordinate (Centralized vs. Swarm).
- **Metrics & Data Collection:** Tracking network compromise levels and agent detection levels over time.

**Major technologies used:**
- **Python 3.10+**
- **Mesa (>= 3.4)** for the core Agent-Based Modeling framework.
- **NetworkX** for defining network topologies.
- **Solara** for the interactive visualization interface (Mesa SolaraViz).

## Running the Simulation
The simulation is executed via `main.py`, which acts as the primary Command Line Interface (CLI).

You can run a headless experiment:
```bash
python main.py --mode experiment --org swarm --trials 5
```

Or you can launch the interactive Solara visualization UI:
```bash
python main.py --mode visualize
```

## Start Here
If you are new to the codebase, we recommend following this reading order:
1. **[Architecture](architecture.md):** Understand the big picture.
2. **[Execution Flow / Lifecycle](lifecycle.md):** Learn how the simulation starts, runs, and terminates.
3. **[Key Classes](classes.md):** Dive into the responsibilities of the main generic components.
4. **[Developer Guide](developer_guide.md):** Learn how to contribute to the code.
