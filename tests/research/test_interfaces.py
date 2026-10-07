"""Bounded native pipeline acceptance, not a scientific experiment matrix."""
import asyncio
import copy
import json
from types import SimpleNamespace

import pytest
import httpx
from backend.app.knowledge import PrivateMemory
from backend.app.policies import candidates, key
from backend.app.research_policy import ResearchPolicy
from backend.app.runs import Run
from backend.app.storage import Store
from packages.contracts.models import EpisodeConfig
from tests.research.helpers import config, TARGET_A


def test_task_identity_does_not_merge_methods_sources_tokens_or_evidence():
    base = {"action": "AttemptAccess", "target": "10.1.1.1", "session": 2, "source_host": "owned", "method": "credential_login", "token_ref": "opaque"}
    variants = [base, dict(base, method="web_rfi", token_ref=None), dict(base, source_host="other"),
                dict(base, token_ref="another"), dict(base, basis_evidence_ids=["Red_0:1"])]
    assert len({key(p) for p in variants}) == len(variants)


def test_delayed_local_token_does_not_arrive_via_raw_intel_view():
    memory = PrivateMemory("Red_0", SimpleNamespace(enabled=True, observation_delay=2, stale_after=8))
    view = {"actor": "Red_0", "sessions": [], "known": {"ip_address": [], "hostname": [], "subnet": []},
            "scan_cache": {}, "catalog": {"version": "minimal_access_v1"}, "possessed_tokens": []}
    memory.observe({"tick": 0, "evidence_id": "Red_0:0", "data": {}}, view)
    raw = dict(view, possessed_tokens=["pending-local"])
    memory.observe({"tick": 1, "evidence_id": "Red_0:1", "data": {"local": {"Research evidence": [{"kind": "artifact", "token_ref": "pending-local"}]}}}, raw)
    memory.accept_intel_view({"view": dict(raw, possessed_tokens=["pending-local", "delivered"]),
                             "address_fragment": {"peer": {"Research evidence": [{"kind": "artifact", "token_ref": "delivered"}]}}})
    assert memory.view["possessed_tokens"] == ["delivered"]
    memory.observe({"tick": 2, "evidence_id": "Red_0:2", "data": {}}, raw)
    assert "pending-local" not in memory.view["possessed_tokens"]
    memory.observe({"tick": 3, "evidence_id": "Red_0:3", "data": {}}, raw)
    assert memory.view["possessed_tokens"] == ["delivered", "pending-local"]
    assert memory.public_view({}, {})["research_evidence"][0]["received_tick"] == 3
    fragment = {"peer": {"Research evidence": [{"kind": "artifact", "token_ref": "delivered"}]}}
    original = {"evidence_id": "Red_1:1", "tick": 1, "data": fragment}
    memory.report(fragment, ["Red_1:1"], "Red_1", 3, [original])
    memory.report(fragment, ["Red_1:1"], "Red_1", 4, [original])
    matching = [r for r in memory.research_evidence if r["evidence_id"] == "Red_1:1"]
    assert len(matching) == 1 and matching[0]["received_tick"] == 3 and matching[0]["observed_tick"] == 1


@pytest.mark.engine
def test_native_private_inputs_candidates_and_complete_controller_mission(tmp_path):
    async def check():
        snapshots = []
        for variant in ("import_enabled", "import_disabled"):
            run = Run(EpisodeConfig.model_validate(config(variant, workers=1, credential_variant="valid")), Store(tmp_path / variant))
            try:
                await run.initialize()
                assert run.meta["feasibility_status"] == "native_witness_validated"
                assert run.frames[0]["tick"] == 0
                view = run.memory["Red_0"].public_view(run.mission(), run.budget())
                snapshots.append((view, candidates(run.memory["Red_0"])))
                forbidden = ("condition_variant", "credential_variant", "research_manifest", "witness", "allowed_sources")
                assert all(s not in json.dumps(snapshots[-1]) for s in forbidden)
                for _ in range(60):
                    if run.meta["status"] == "completed":
                        break
                    await run.advance()
                assert run.frames[-1]["score"]["mission_success"], [(f["tick"], f["actions"]) for f in run.frames[-5:]]
                assert TARGET_A in run.frames[-1]["score"]["privileged_hosts"]
                assert run.cognition.summary()["calls"] == 0
                altered = copy.deepcopy(view)
                altered["truth"] = {"hidden": "oracle"}
                options = snapshots[-1][1]
                assert ResearchPolicy("evidence_controller").rank(view, options, 1) == ResearchPolicy("evidence_controller").rank(altered, options, 1)
            finally:
                await run.stop()
        assert snapshots[0] == snapshots[1]
    asyncio.run(check())


@pytest.mark.engine
def test_mock_provider_decisions_use_native_gateway_and_public_input(tmp_path, monkeypatch):
    policy = ResearchPolicy("evidence_controller")
    requests = []
    class Response:
        def __init__(self, proposal):
            self.proposal = proposal
        def raise_for_status(self):
            pass
        def json(self):
            return {"model": "mock-only", "message": {"content": json.dumps(self.proposal)},
                    "prompt_eval_count": 10, "eval_count": 4}
    class Client:
        def __init__(self, **kwargs):
            pass
        async def __aenter__(self):
            return self
        async def __aexit__(self, *args):
            pass
        async def post(self, url, json):
            view = __import__('json').loads(json['messages'][1]['content'])
            requests.append(view)
            options, _ = policy.rank(view, view['eligible_candidates'], view['native'].get('pending_action', {}).get('started_tick', 0) if view['native'].get('pending_action') else len(requests))
            return Response(options[0] if options else {"action": "Sleep"})
    monkeypatch.setattr(httpx, "AsyncClient", Client)
    async def check():
        cfg = config(workers=1, credential_variant="valid")
        cfg['cognition'].update(provider='ollama', model='mock-only', scripted_policy='legacy', max_context_bytes=128000, max_team_tokens=1000000)
        run = Run(EpisodeConfig.model_validate(cfg), Store(tmp_path))
        try:
            await run.initialize()
            for _ in range(40):
                if run.meta['status']=='completed':
                    break
                await run.advance()
            assert run.frames[-1]['score']['mission_success']
            assert run.cognition.calls == len(requests) and run.cognition.used == len(requests)*14
            assert all(v['native']['catalog']['version']=='minimal_access_v1' for v in requests)
            assert all('condition_variant' not in json.dumps(v) and 'research_truth' not in json.dumps(v) for v in requests)
        finally:
            await run.stop()
    asyncio.run(check())


@pytest.mark.engine
@pytest.mark.parametrize("architecture,workers", [("hierarchy", 2), ("swarm", 4), ("hierarchy", 4), ("swarm", 2)])
def test_native_organizations_merge_capabilities_from_split_entry(tmp_path, architecture, workers):
    async def check():
        cfg = config(recipe="combine", architecture=architecture, workers=workers, initial_access="matched_split_entry")
        run = Run(EpisodeConfig.model_validate(cfg), Store(tmp_path / architecture))
        try:
            await run.initialize()
            for _ in range(cfg["schedule"]["max_ticks"]):
                if run.meta["status"] in ("completed", "errored"):
                    break
                await run.advance()
            assert run.frames[-1]["score"]["mission_success"], [(f["tick"], [(a["actor"], a["proposal"], a["outcome"]) for a in f["actions"]]) for f in run.frames[-5:]]
            events = [json.loads(s) for s in (run.directory / "events.jsonl").read_text().splitlines()]
            assert any(e["type"] == "intel_delivery" and any(r.get("token_ref") for fields in e["address_fragment"].values() for r in fields.get("Research evidence", [])) for e in events)
            if architecture == "hierarchy":
                assert "Coordinator" not in run.frames[-1]["private_views"]
                assert all(m["kind"] in ("report", "assignment") for m in run.frames[-1]["messages"])
            else:
                assert all(m["sender"] != "Coordinator" and m["kind"] == "claim" for m in run.frames[-1]["messages"])
        finally:
            await run.stop()
    asyncio.run(check())


@pytest.mark.engine
@pytest.mark.parametrize('architecture,workers,access,delay', [
    ('hierarchy',2,'matched_split_entry',2),('swarm',2,'matched_split_entry',2),
    ('hierarchy',4,'common_entry',0),('swarm',4,'common_entry',0)])
def test_native_permuted_organizations_and_public_transport_delay(tmp_path, architecture, workers, access, delay):
    async def check():
        # Opposite bridge/archive role assignment to default recipe seed401.
        import random
        for seed in range(20):
            order=[1,2]
            random.Random(f'recipe-v1:{seed}').shuffle(order)
            if order==[1,2]:break
        else:raise AssertionError('Opposite role permutation unavailable')
        cfg=config(recipe='combine',architecture=architecture,workers=workers,initial_access=access,
                   seed_namespaces={'recipe':seed,'event':701})
        cfg['communication']['extra_delay']=delay
        run=Run(EpisodeConfig.model_validate(cfg),Store(tmp_path))
        try:
            await run.initialize()
            assert run.frames[0]['truth']['research_truth']['roles']['bridge'].endswith('_1')
            for _ in range(cfg['schedule']['max_ticks']):
                if run.meta['status'] in ('completed','errored'):break
                await run.advance()
            assert run.frames[-1]['score']['mission_success'], (run.meta['termination_reason'],run.meta['metrics'])
            assert run.cognition.calls==0
            events=[json.loads(row) for row in (run.directory/'events.jsonl').read_text(encoding='utf-8').splitlines()]
            assert any(e['type']=='intel_delivery' for e in events)
            assert all(m['resolved_tick']>=m['created_tick']+1+delay for m in run.frames[-1]['messages'] if m['status']=='delivered')
            assert run.frames[-1]['views']['Red_0']['access_resources']['reserved']<=12
        finally:
            await run.stop()
    asyncio.run(check())
