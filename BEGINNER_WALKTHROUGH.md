# BEGINNER WALKTHROUGH: ABMS Cyber Simulation

This is a practical, step-by-step tutorial.

Goal:
- Run the simulation from command line.
- Run multiple trials.
- Launch the visualization UI.
- Inspect the exact files that control each behavior.

Assumption:
- You are in the project root folder:
  - `c:\Users\sasok\OneDrive\Grad project\AbstractCyberSim`

---

## 1. Environment Setup

## Step 1: Create and activate a virtual environment

Run:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Inspect:
- Your prompt should show `(.venv)`.

If activation is blocked by policy, run PowerShell as admin once and set policy:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

## Step 2: Install dependencies

Run:

```powershell
pip install -r requirements.txt
```

Inspect:
- Make sure packages install, especially:
  - `mesa`
  - `networkx`
  - `pandas`
  - `solara`

---

## 2. First Simulation Run (Experiment Mode)

## Step 3: Run one swarm trial

Run:

```powershell
python main.py --mode experiment --org swarm --trials 1
```

Inspect expected output pattern:

```text
Running Experiment: swarm for 1 trials
Trial 1: Steps=..., Detection=..., Compromised=...
```

What happened internally:
- `main.py` parsed CLI arguments.
- `run_experiment()` created `CyberModel`.
- Model loop ran until `model.running` became `False`.

Inspect code now:
- `main.py`: entry point and loop.
- `abms_cyber/model/cyber_model.py`: model lifecycle.

---

## Step 4: Run multiple trials

Run:

```powershell
python main.py --mode experiment --org swarm --trials 5
```

Inspect:
- You should see 5 trial summary lines.
- Compare `Steps`, `Detection`, and `Compromised` across trials.

Why results vary:
- Randomness in exploit attempts and network generation.
- Controlled partly by seed in config.

Inspect code now:
- `abms_cyber/config/default_config.py` (`random_seed`, `max_steps`, etc.)
- `abms_cyber/environment/network_graph.py` (random node properties)
- `abms_cyber/agents/cyber_agent.py` (`exploit` random success)

---

## 3. Compare Organization Modes

## Step 5: Run centralized mode

Run:

```powershell
python main.py --mode experiment --org centralized --trials 1
```

Inspect:
- Command should run.
- Results may look similar to swarm for now.

Important reason:
- Centralized logic is currently mostly a placeholder.

Inspect code now:
- `abms_cyber/organization/centralized.py`
- `abms_cyber/organization/swarm.py`

---

## 4. Open the Visualization UI

## Step 6: Start visualization mode

Run:

```powershell
python main.py --mode visualize --org swarm
```

Inspect:
- Terminal should print: `Launching Solara Visualization UI...`
- A Solara server starts (usually localhost URL appears in terminal).
- Open the URL in browser.

---

## Step 7: Use UI controls

In the page:
- Click `Step` repeatedly.
- Watch changes:
  - Detection level increases on failed exploits.
  - Compromised nodes count changes.
  - Agents move as triangles.
- Click `Reset` to restart.

Inspect code now:
- `abms_cyber/visualization/app.py` (buttons and page)
- `abms_cyber/visualization/network_view.py` (graph rendering)
- `abms_cyber/visualization/charts.py` (metrics chart)
- `abms_cyber/visualization/portrayal.py` (node/agent colors/sizes)

---

## 5. Understand Agent Decisions by Reading in Sequence

Read these files in order:

1. `abms_cyber/agents/cognition/base_cognition.py`
2. `abms_cyber/agents/cognition/rule_based.py`
3. `abms_cyber/agents/cyber_agent.py`
4. `abms_cyber/agents/memory.py`

What to inspect:
- `decide()` returns strings like `SCAN:3`.
- `execute_action()` maps those strings to method calls.
- Memory updates after each action.

---

## 6. Understand Stop Conditions

## Step 8: Find where simulation ends

Inspect file:
- `abms_cyber/model/cyber_model.py`

Focus method:
- `_check_termination()`

Current stop conditions:
- Target compromised + at least one agent has required privilege.
- Detection level reached max.
- Step count reached max steps.

---

## 7. Quick Mini Exercises (Hands-On)

## Exercise A: Make simulation shorter

Edit:
- `abms_cyber/config/default_config.py`

Change:
- `max_steps: int = 100` -> `max_steps: int = 20`

Run again:

```powershell
python main.py --mode experiment --org swarm --trials 1
```

Inspect:
- Trial should end in <= 20 steps.

---

## Exercise B: Increase number of agents

Edit:
- `abms_cyber/config/default_config.py`

Change:
- `num_agents: int = 5` -> `num_agents: int = 10`

Run:

```powershell
python main.py --mode experiment --org swarm --trials 3
```

Inspect:
- Compare compromised node counts and detection progression.

---

## Exercise C: Make escalation easier

Edit:
- `abms_cyber/agents/cyber_agent.py`, method `escalate()`.

Change:
- probability from `0.5` to `0.9`.

Run:

```powershell
python main.py --mode experiment --org swarm --trials 3
```

Inspect:
- Higher chance of admin privilege should affect success condition speed.

---

## 8. Common Beginner Troubleshooting

## Problem: `ModuleNotFoundError`

Fix:
- Ensure you run from project root.
- Ensure `.venv` is activated.
- Reinstall requirements.

## Problem: Solara visualization does not open

Fix:
- Check terminal for localhost URL and open manually.
- Confirm `solara` installed.

## Problem: No visible behavior change in centralized mode

Reason:
- `CentralizedOrganization` is not fully implemented yet.

---

## 9. Suggested Learning Order

1. `main.py`
2. `abms_cyber/model/cyber_model.py`
3. `abms_cyber/environment/network_graph.py`
4. `abms_cyber/agents/cognition/rule_based.py`
5. `abms_cyber/agents/cyber_agent.py`
6. Visualization files

This order matches runtime flow.

---

## 10. What To Build Next (Beginner Path)

1. Fully implement `centralized.py` leader behavior.
2. Move hardcoded probabilities to config and use them everywhere.
3. Add tests for `move`, `exploit`, and termination logic.
4. Write a richer cognition strategy (risk-aware or target-focused).
