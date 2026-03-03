# Key Classes and Responsibilities

Understanding the key definitions is essential when studying the `abms_cyber` package.

## Core Simulation Framework
### `CyberModel` (Model)
- **Represents:** The global state of the simulation.
- **Responsibilities:** Setting up the network/agents, progressing the clock ticks, calculating the win/loss condition.
- **Do:** Use `config` variables provided to it to set the simulation constraints.
- **Do Not:** Put agent-specific rules inside the model loop.

### `NetworkEnvironment`
- **Represents:** The physical structure attackers are traversing.
- **Responsibilities:** Wrapping the NetworkX graph and managing `CyberNode` translation.
- **Do:** Call `get_random_start_node()` and `get_node(id)` to retrieve verified node details.
- **Do Not:** Let agents edit the underlying dictionary of nodes directly.

## Cyber Agents
### `CyberAgent`
- **Represents:** A singular attacking persona traversing the network.
- **Responsibilities:** Making a single move/action per `step()` tick via `execute_action(action_string)`.
- **Public Methods:** `move()`, `scan()`, `exploit()`, `escalate()`.
- **Do Not:** Overcomplicate `execute_action()` code. Logic on *which* action to take should remain strictly in its `Cognition` attribute.

### `AgentMemory`
- **Represents:** The isolated knowledge base an agent has built.
- **Responsibilities:** Recording visited paths, compromised nodes, and actions over time.
- **Do:** Reference memory during `decide()` methods in Cognition instead of querying the main Model.
- **Do Not:** Give the agent memory elements it hasn't successfully `SCAN`ned or `EXPLOIT`ed.

### `BaseCognition` / `RuleBasedCognition`
- **Represents:** The intelligence / decision logic ruleset of the agent.
- **Responsibilities:** Choosing an action protocol (e.g. `"EXPLOIT:3"`) based on `current_node` and memory inputs.
- **Public Methods:** `decide(self) -> str`

## Organization Models
### `BaseOrganization` (and `Centralized` / `Swarm` variants)
- **Represents:** Coordination logic. Sub-agents may or may not decide independently.
- **Responsibilities:** Intervening right before the execution of agent loops to define global strategies and priorities.
