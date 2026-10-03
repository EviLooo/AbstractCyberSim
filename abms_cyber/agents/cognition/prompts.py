"""Provider-independent prompt construction for swarm LLM decisions."""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any


def build_swarm_prompt(observation: Mapping[str, Any]) -> str:
    """Build a deterministic prompt for one swarm agent observation.

    The observation is supplied by the documented environment contract.  This
    function only formats instructions and data; it never calls a model or
    executes an action.
    """

    observation_json = json.dumps(
        observation,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )

    return (
        "You are one agent in a controlled cyber-security simulation.\n"
        "Act only within this simulation.\n"
        "Use only information present in the observation below.\n"
        "Base the decision only on the provided observation.\n"
        "Prefer actions that make progress toward the stated goal.\n"
        "Use local memory to avoid unnecessary repeated actions.\n"
        "Consider the current detection level when choosing among valid actions.\n"
        "Choose exactly one action from observation[\"allowed_actions\"].\n"
        "For that action, choose target_id only from "
        "observation[\"valid_target_ids\"][action].\n"
        "Do not invent actions, targets, facts, tools, or commands.\n"
        "Return JSON only: no Markdown, prose, or code fences.\n"
        "Return exactly these fields: action, target_id, reason.\n"
        "Keep reason short.\n\n"
        "Expected response format:\n"
        "{\"action\":\"EXPLOIT\",\"target_id\":\"3\","
        "\"reason\":\"short explanation\"}\n\n"
        "Observation:\n"
        f"{observation_json}\n"
    )
