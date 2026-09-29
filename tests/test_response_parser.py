import json

import pytest

from abms_cyber.agents.cognition.response_parser import (
    ParsedAction,
    ResponseValidationError,
    parse_llm_response,
)


def response(**overrides):
    value = {
        "action": "EXPLOIT",
        "target_id": "3",
        "reason": "The current node is scanned and not compromised.",
    }
    value.update(overrides)
    return json.dumps(value)


def test_valid_response_is_parsed_without_execution():
    parsed = parse_llm_response(response(), allowed_target_ids={"3", "4"})

    assert parsed == ParsedAction(
        action="EXPLOIT",
        target_id="3",
        reason="The current node is scanned and not compromised.",
    )


@pytest.mark.parametrize("action", ["SCAN", "MOVE", "EXPLOIT", "ESCALATE"])
def test_all_allowed_actions_are_accepted(action):
    assert parse_llm_response(response(action=action)).action == action


@pytest.mark.parametrize("raw", [
    "not json",
    "[]",
    "null",
    "{\"action\": \"EXPLOIT\"",
])
def test_invalid_json_or_shape_fails_safely(raw):
    with pytest.raises(ResponseValidationError):
        parse_llm_response(raw)


@pytest.mark.parametrize("missing", ["action", "target_id", "reason"])
def test_required_fields_are_required(missing):
    value = json.loads(response())
    del value[missing]

    with pytest.raises(ResponseValidationError):
        parse_llm_response(json.dumps(value))


def test_invented_action_is_rejected():
    with pytest.raises(ResponseValidationError):
        parse_llm_response(response(action="DELETE_EVERYTHING"))


@pytest.mark.parametrize("target_id", [None, "", "   ", 3, []])
def test_invalid_target_id_is_rejected(target_id):
    with pytest.raises(ResponseValidationError):
        parse_llm_response(response(target_id=target_id))


def test_unknown_target_id_is_rejected_when_allowed_ids_are_provided():
    with pytest.raises(ResponseValidationError):
        parse_llm_response(response(target_id="99"), allowed_target_ids={"3", "4"})


@pytest.mark.parametrize("reason", [None, "", "   ", 123])
def test_missing_or_invalid_reason_is_rejected(reason):
    with pytest.raises(ResponseValidationError):
        parse_llm_response(response(reason=reason))


def test_extra_fields_are_rejected():
    with pytest.raises(ResponseValidationError):
        parse_llm_response(response(untrusted_code="print('should never run')"))
