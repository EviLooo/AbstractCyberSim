# LLM Environment Contract

This document is the handoff from Student 1 to Student 2. It defines how cognition reads the cyber world and how a chosen action is safely applied.

## The two interfaces

Build an observation before asking an LLM to decide:

```python
from abms_cyber.environment.observation import build_observation

observation = build_observation(agent, model)
```

Resolve the validated LLM response through the model's trusted gateway:

```python
result = model.action_resolver.resolve(
    agent,
    {"action": "SCAN", "target_id": "3"},
)
```

`result` is an `ActionResult`. Use `result.to_dict()` when JSON data is needed.

## Observation fields

| Field | Meaning |
| --- | --- |
| `agent_id` | Mesa's id for the deciding agent, represented as a string. |
| `organization` | `swarm` or `centralized`. |
| `step`, `max_steps` | Current time and episode limit. |
| `goal` | Plain-language objective for the cognition module. |
| `current_node` | Node where the agent is located. |
| `privilege_level`, `required_privilege` | Current and goal privilege values. |
| `detection_level`, `max_detection_level` | Current detection risk and failure limit. |
| `local_memory` | This agent's known, scanned and compromised nodes plus recent actions. |
| `network` | Full graph topology and JSON-ready node state, matching the current requirement. |
| `allowed_actions` | Actions that currently have at least one valid target. |
| `valid_target_ids` | Allowed target ids for each action. |
| `response_format` | Reminder of the three fields expected from cognition. |

Student 2 should keep prompts compact. If the observation becomes too large later, add a separate summarized observation mode instead of silently removing fields.

## Action request

The resolver accepts any of these equivalent forms:

```python
"EXPLOIT:3"
```

```python
{"action": "EXPLOIT", "target_id": "3"}
```

```python
ActionRequest(action=ActionType.EXPLOIT, target_id="3")
```

Never execute arbitrary Python or tool names returned by an LLM. Pass only the validated action and target to the resolver.

## Action rules

| Action | Current rule |
| --- | --- |
| `SCAN` | Target must be the current node. It always completes and marks the node scanned. |
| `EXPLOIT` | Target must be the current node. Success probability equals `vulnerability_level`. |
| `ESCALATE` | Target must be the compromised current node. Success probability comes from config. |
| `MOVE` | Target must be a direct neighbor. By default, the current/source node must already be compromised. |

All detection changes and probabilities are in `CyberConfig`. Invalid actions never change simulation state.

## Action result

`ActionResult` contains:

- `action` and `target_id`
- `valid`: whether the request obeyed environment rules
- `success`: whether a valid probabilistic action succeeded
- `reason`: short text safe for memory and debugging
- `detection_delta`: actual increase after clamping
- `state_changes`: JSON-ready details such as the new node or privilege level

`valid=False` is different from `success=False`. For example, exploiting a remote node is invalid, while attempting an allowed exploit that fails its probability roll is valid but unsuccessful.

## Student 2 integration checklist

1. Build the observation with `build_observation`.
2. Send a compact prompt and require one JSON object containing `action`, `target_id`, and `reason`.
3. Parse JSON without using `eval` or `exec`.
4. Check the action and target against `allowed_actions` and `valid_target_ids`.
5. Call `model.action_resolver.resolve(agent, parsed_action)`.
6. Record the request, short LLM reason, and `ActionResult` in agent memory.
7. Treat `valid=False` as an invalid LLM response metric.
8. Use the small rule-based policy only when API calls or validation fail.

## Verification command

From the repository root:

```powershell
conda run -n mesa3 python -m unittest discover -s tests -v
```

The local machine currently has a `mesa3` environment with Mesa 3.4.2. The older project note that names the environment `mesa` does not match the installed environments.
