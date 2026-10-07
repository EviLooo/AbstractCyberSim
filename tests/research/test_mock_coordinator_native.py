"""Mock provider responses over delivered inputs, through the real native loop."""
import asyncio
import json

import httpx
import pytest

from backend.app.research_policy import ResearchPolicy
from backend.app.runs import Run
from backend.app.storage import Store
from packages.contracts.models import EpisodeConfig
from tests.research.helpers import config


@pytest.mark.engine
def test_mock_leader_and_workers_use_only_their_actual_input(tmp_path, monkeypatch):
    requests, policies = [], {}

    class Response:
        def __init__(self, decision):
            self.decision = decision

        def raise_for_status(self):
            pass

        def json(self):
            return {"model": "mock-only", "message": {"content": json.dumps(self.decision)},
                    "prompt_eval_count": 10, "eval_count": 4}

    class Client:
        def __init__(self, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def post(self, url, json):
            supplied = __import__('json').loads(json['messages'][1]['content'])
            requests.append(supplied)
            if supplied.get('role') != 'coordinator':
                return Response(supplied['suggested_action'])
            assignments = {}
            for report in supplied['delivered_reports']:
                actor, data = report['sender'], report['payload']
                if data.get('pending_action'):
                    continue
                hosts, cache = {}, {}
                for evidence in data['research_evidence']:
                    for lead in evidence.get('leads', []) + ([evidence['lead']] if evidence.get('lead') else []):
                        hosts[lead['address']] = {'fields': {'System info': {'Hostname': lead['hostname']}}}
                # The delivered candidate list itself declares owned scan eligibility.
                for option in data['candidates']:
                    if option['action']=='AttemptAccess':
                        cache.setdefault(str(option['session']), {})[option['target']] = [80, 22]
                view = {'mission': supplied['mission'], 'belief_epoch': data['belief_epoch'],
                        'hosts': hosts, 'reported_hosts': {}, 'history': data['recent_actions'],
                        'research_evidence': data['research_evidence'], 'inbox': [],
                        'native': {'catalog': data['catalog'], 'sessions': data['sessions'],
                                   'scan_cache': cache, 'possessed_tokens': data['possessed_tokens']}}
                policy = policies.setdefault(actor, ResearchPolicy('evidence_controller'))
                options, _ = policy.rank(view, data['candidates'], supplied['tick'])
                assignments[actor] = options[0] if options else None
            return Response(assignments)

    monkeypatch.setattr(httpx, 'AsyncClient', Client)

    async def check():
        cfg = config(workers=2, architecture='hierarchy', credential_variant='valid')
        cfg['cognition'].update(provider='ollama', model='mock-only', scripted_policy='legacy',
                                max_context_bytes=128000, max_team_tokens=2000000)
        run = Run(EpisodeConfig.model_validate(cfg), Store(tmp_path))
        try:
            await run.initialize()
            for _ in range(70):
                if run.meta['status']=='completed':
                    break
                await run.advance()
            assert run.frames[-1]['score']['mission_success']
            leaders = [v for v in requests if v.get('role')=='coordinator']
            assert leaders and all('native' not in v and 'truth' not in v for v in leaders)
            assert all(v['catalog']['version']=='minimal_access_v1' for v in leaders)
            assert all('condition_variant' not in json.dumps(v) and 'research_truth' not in json.dumps(v) for v in requests)
            assert run.cognition.used==len(requests)*14 and run.cognition.calls==len(requests)
            assert 'Coordinator' not in run.frames[-1]['private_views']
        finally:
            await run.stop()
    asyncio.run(check())
