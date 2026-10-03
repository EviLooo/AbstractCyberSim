"""Mocked transport only: no installed model or external provider is contacted."""
import asyncio
import json
import httpx
import pytest
from backend.app.providers import BudgetExceeded, Cognition
from packages.contracts.models import CognitionConfig


def test_format_repair_is_bounded_and_both_calls_are_charged(tmp_path, monkeypatch):
    replies = ["{bad JSON", json.dumps({"action": "Sleep", "rationale": "No eligible task"})]
    requests = []

    class Response:
        def raise_for_status(self):
            pass

        def json(self):
            return {"model": "fixture", "message": {"content": replies.pop(0)}, "prompt_eval_count": 10, "eval_count": 4}

    class Client:
        def __init__(self, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def post(self, url, json):
            requests.append(json)
            return Response()

    monkeypatch.setattr(httpx, "AsyncClient", Client)
    cognition = Cognition(CognitionConfig(provider="ollama", model="fixture"), tmp_path / "transcript.jsonl")
    result = asyncio.run(cognition.worker("Red_0", {"actor": "Red_0", "native": {"known": {}}}, {"action": "Sleep"}))
    assert result["action"] == "Sleep"
    assert cognition.used == 28 and cognition.calls == 2
    assert len(requests) == 2
    transcripts = [json.loads(l) for l in cognition.path.read_text().splitlines()]
    assert transcripts[1]["input"]["format_repair"]
    assert [r["charged_tokens"] for r in transcripts] == [14, 14]


def test_insufficient_budget_makes_no_call(tmp_path, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Transport must not be contacted")
    monkeypatch.setattr(httpx, "AsyncClient", forbidden)
    cognition = Cognition(CognitionConfig(provider="ollama", model="fixture", max_team_tokens=1000), tmp_path / "transcript.jsonl")
    with pytest.raises(BudgetExceeded):
        asyncio.run(cognition.worker("Red_0", {}, {"action": "Sleep"}))
    assert cognition.calls == 0


def test_unknown_usage_after_transport_error_is_never_recorded_as_free(tmp_path, monkeypatch):
    class Client:
        def __init__(self, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def post(self, *args, **kwargs):
            raise httpx.ConnectError("fixture transport failure")

    monkeypatch.setattr(httpx, "AsyncClient", Client)
    cognition = Cognition(CognitionConfig(provider="ollama", model="fixture"), tmp_path / "transcript.jsonl")
    with pytest.raises(httpx.ConnectError):
        asyncio.run(cognition.worker("Red_0", {}, {"action": "Sleep"}))
    assert cognition.used > 0 and cognition.unknown_usage == 1
    assert cognition.calls == 1 and cognition.failures == 1
    record = json.loads(cognition.path.read_text())
    assert record["usage_status"] == "unknown_reserved"
