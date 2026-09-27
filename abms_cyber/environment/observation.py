"""Build compact, JSON-ready observations for rule-based or LLM cognition."""

from typing import Any

from abms_cyber.environment.action_resolver import ActionType


def build_observation(agent: Any, model: Any) -> dict[str, Any]:
    """Return the documented observation contract consumed by cognition modules."""
    current = agent.current_node
    history_limit = model.config.observation_history_limit
    memory = getattr(agent, "memory", None)

    known_nodes = _sorted_ids(getattr(memory, "known_nodes", set()))
    scanned_nodes = _sorted_ids(getattr(memory, "scanned_nodes", set()))
    compromised_nodes = _sorted_ids(
        getattr(memory, "compromised_nodes", set())
    )
    history = list(getattr(memory, "action_history", []))
    recent_actions = history[-history_limit:] if history_limit else []

    nodes = [
        model.network.nodes[node_id].to_dict()
        for node_id in _sorted_ids(model.network.nodes.keys())
    ]
    valid_targets = _valid_targets(agent, model)
    allowed_actions = [
        action.value
        for action in ActionType
        if valid_targets[action.value]
    ]

    return {
        "agent_id": str(agent.unique_id),
        "organization": model.org_type,
        "step": int(model.steps),
        "max_steps": model.config.max_steps,
        "goal": "Compromise the target and obtain the required privilege",
        "current_node": current.id,
        "privilege_level": agent.privilege_level,
        "required_privilege": model.config.required_privilege,
        "detection_level": round(float(model.detection_level), 4),
        "max_detection_level": model.config.max_detection_level,
        "local_memory": {
            "known_nodes": known_nodes,
            "scanned_nodes": scanned_nodes,
            "compromised_nodes": compromised_nodes,
            "recent_actions": recent_actions,
        },
        "network": {
            "visibility": "full_topology",
            "nodes": nodes,
        },
        "allowed_actions": allowed_actions,
        "valid_target_ids": valid_targets,
        "response_format": {
            "action": "one value from allowed_actions",
            "target_id": "one id allowed for that action",
            "reason": "short explanation",
        },
    }


def _valid_targets(agent: Any, model: Any) -> dict[str, list[str]]:
    current = agent.current_node
    can_move = (
        current.compromised
        or not model.config.move_requires_compromised_source
    )
    return {
        ActionType.MOVE.value: _sorted_ids(current.neighbors) if can_move else [],
        ActionType.SCAN.value: [current.id],
        ActionType.EXPLOIT.value: [] if current.compromised else [current.id],
        ActionType.ESCALATE.value: (
            [current.id]
            if current.compromised
            and agent.privilege_level < model.config.required_privilege
            else []
        ),
    }


def _sorted_ids(values: Any) -> list[str]:
    ids = [str(value) for value in values]
    return sorted(ids, key=lambda value: (0, int(value)) if value.isdigit() else (1, value))
