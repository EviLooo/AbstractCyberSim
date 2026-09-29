"""Strict parsing and validation for LLM action responses.

This module deliberately has no simulation or execution behavior.  It only
converts a JSON response into a validated action value.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from collections.abc import Collection


ALLOWED_ACTIONS = frozenset({"SCAN", "MOVE", "EXPLOIT", "ESCALATE"})
_REQUIRED_FIELDS = frozenset({"action", "target_id", "reason"})


class ResponseValidationError(ValueError):
    """Raised when an LLM response does not match the safe action format."""


@dataclass(frozen=True)
class ParsedAction:
    """The validated, non-executable representation of an LLM decision."""

    action: str
    target_id: str
    reason: str


def parse_llm_response(
    raw_response: str,
    *,
    allowed_target_ids: Collection[str] | None = None,
) -> ParsedAction:
    """Parse and validate one JSON action response.

    ``allowed_target_ids`` is optional so this parser remains independent of
    Student 1's environment.  When supplied, the target must be one of the
    caller-provided IDs.  This function never evaluates or executes response
    content.
    """

    if not isinstance(raw_response, str):
        raise ResponseValidationError("response must be a JSON string")

    try:
        decoded = json.loads(raw_response)
    except (json.JSONDecodeError, TypeError) as exc:
        raise ResponseValidationError("response is not valid JSON") from exc

    if not isinstance(decoded, dict):
        raise ResponseValidationError("response must be a JSON object")

    fields = set(decoded)
    missing = _REQUIRED_FIELDS - fields
    if missing:
        missing_fields = ", ".join(sorted(missing))
        raise ResponseValidationError(f"missing required field(s): {missing_fields}")

    extra = fields - _REQUIRED_FIELDS
    if extra:
        extra_fields = ", ".join(sorted(extra))
        raise ResponseValidationError(f"unexpected field(s): {extra_fields}")

    action = decoded["action"]
    if not isinstance(action, str) or action not in ALLOWED_ACTIONS:
        raise ResponseValidationError("action is not allowed")

    target_id = decoded["target_id"]
    if not isinstance(target_id, str) or not target_id.strip():
        raise ResponseValidationError("target_id must be a non-empty string")
    if allowed_target_ids is not None and target_id not in allowed_target_ids:
        raise ResponseValidationError("target_id is not allowed")

    reason = decoded["reason"]
    if not isinstance(reason, str) or not reason.strip():
        raise ResponseValidationError("reason must be a non-empty string")

    return ParsedAction(action=action, target_id=target_id, reason=reason)
