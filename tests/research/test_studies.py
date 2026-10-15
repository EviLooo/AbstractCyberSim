"""Bounded split/freeze acceptance; no scientific sweep or live provider."""
import asyncio
import copy
import json
import random
import hashlib
import zipfile

import pytest

from backend.app.batches import Batch
from backend.app.evaluation import expand, compare_runs
from backend.app.runs import Run
from backend.app.storage import Store
from backend.app.studies import Study, causal_world, condition_configuration, model_artifact
from packages.contracts.models import EpisodeConfig, ExperimentSpec
from tests.research.helpers import config


def branch_seed(reverse):
    for seed in range(20):
        order = [1,2]
        random.Random('recipe-v1:{}'.format(seed)).shuffle(order)
        if (order[0]==2)==reverse:
            return seed
    raise AssertionError('Fixture role permutation unavailable')


@pytest.mark.engine
def test_native_split_freeze_binding_and_one_bounded_queue_job(tmp_path, monkeypatch):
    async def check():
        store, refs, configurations = Store(tmp_path), [], []
        # Known rules/placements in development; test withholds their combination.
        fixtures = [('import_enabled',False,'development'),('import_disabled',True,'development'),
                    ('import_enabled',True,'validation'),('import_disabled',False,'test')]
        for variant,reverse,split in fixtures:
            cfg = config(variant=variant,workers=1,credential_variant='valid',
                         seed_namespaces={'recipe':branch_seed(reverse),'event':701})
            run = Run(EpisodeConfig.model_validate(cfg),store)
            try:
                await run.initialize()
                assert run.meta['tick']==0 and run.meta['feasibility_status']=='native_witness_validated'
                refs.append({'run_id':run.id,'split':split})
                configurations.append(cfg)
            finally:
                await run.stop()
        study = Study.create(store,{'name':'Software split acceptance','worlds':refs})
        frozen = study.check_sources()
        assert frozen['payload']['purpose']=='software_qualification'
        test_world = study.bind(configurations[-1],'test')
        assert test_world['causal_world']['variant']=='import_disabled'
        unfrozen=copy.deepcopy(configurations[-1])
        unfrozen['schedule']['mode']='team_cap_one'
        with pytest.raises(ValueError,match='not frozen'):
            study.bind(unfrozen,'test')
        unfrozen=copy.deepcopy(configurations[-1])
        unfrozen['communication']['extra_delay']=2
        with pytest.raises(ValueError,match='not frozen'):
            study.bind(unfrozen,'test')
        leakage = copy.deepcopy(refs)
        leakage[-1]['run_id'] = refs[0]['run_id']
        with pytest.raises(ValueError,match='leakage'):
            Study.create(store,{'name':'Invalid split','worlds':leakage})
        renamed = copy.deepcopy(test_world['world']['snapshot'])
        for notes in renamed['research_truth']['artifacts'].values():
            for note in notes:
                if 'lead' in note['public']:
                    note['public']['lead']['address']='192.0.2.77'
        assert causal_world(renamed,configurations[-1])==test_world['causal_world']
        planned = expand(ExperimentSpec.model_validate({'base':configurations[-1],
                    'architectures':['independent'],'worker_counts':[1],'world_seeds':[100]}))
        batch = Batch.create(store,planned,freeze_id=study.id,split='test')
        result = await batch.execute(max_jobs=1)
        attempt = result['jobs'][0]['attempts'][0]
        assert attempt['status']=='completed' and attempt['metrics']['success']
        meta = store.get(attempt['run_id'])
        assert meta['freeze_id']==study.id and meta['causal_world_hash']==test_world['causal_world_hash']
        assert (store.path(meta['id'])/'freeze-binding.json').is_file()
        from backend.app.exports import export_study
        exported = export_study(store,study.id,tmp_path/'study.zip')
        assert exported['runs']==1 and exported['analysis_source_matches_freeze']
        with zipfile.ZipFile(exported['path']) as bundle:
            checksums = json.loads(bundle.read('checksums.json'))
            assert all(hashlib.sha256(bundle.read(name)).hexdigest()==expected for name,expected in checksums.items())
            analysis = json.loads(bundle.read('analysis.json'))
            assert analysis['analyses']['test']['paired_worlds']==0
            assert json.loads(bundle.read('reproduction.json'))['frozen_source_complete']
            assert 'source/backend/app/research_metrics.py' in bundle.namelist()
            assert 'figures/test/paired-contrasts.svg' in bundle.namelist()
            assert 'No eligible paired' in bundle.read('figures/test/paired-contrasts.svg').decode()
        compare = compare_runs([meta],[meta['id']])
        assert not compare['paired_worlds'] and compare['excluded']
        monkeypatch.setattr('backend.app.studies.source_manifest',lambda:{'modified.py':'changed'})
        with pytest.raises(ValueError,match='changed after freeze'):
            await batch.execute(max_jobs=1)
        document = study.read()
        document['payload']['name']='tampered'
        store.write_json(study.path,document)
        with pytest.raises(ValueError,match='immutable'):
            study.read()
    asyncio.run(check())


def test_failure_aware_pairing_and_conservative_world_clusters():
    def row(identity,architecture,world,pair,success):
        return {'id':identity,'profile':'enterprise_cc4_research','freeze_id':'f',
            'freeze_purpose':'proposed_study','split':'test','causal_world_hash':world,
            'condition_hash':pair,'pair_key':pair,'feasibility_status':'native_witness_validated',
            'status':'completed','manual_intervention':False,'purpose':'evaluation',
            'architecture':architecture,'termination_reason':'mission_success' if success else 'tick_limit',
            'metrics':{'success':success,'charged_tokens':10,'declared_horizon':100,'research_formula_version':'research_metrics_v1.1',
                       'restricted_completion_ticks':20 if success else 100}}
    rows = [row('a','hierarchy','world1','pair1',True),row('b','swarm','world1','pair1',False),
            row('c','hierarchy','world1','pair2',True),row('d','swarm','world1','pair2',False),
            row('e','hierarchy','world2','pair3',False),row('f','swarm','world2','pair3',True),
            row('g','independent','world2','diagnostic',True)]
    result = compare_runs(rows,[r['id'] for r in rows])
    assert result['paired_worlds']==2 and result['paired_conditions']==3 and result['paired_episodes']==6
    assert result['success_difference']==0
    assert result['estimates']['restricted_completion_difference']['estimate']==0
    assert result['outcome_counts']=={'mission_success':4,'tick_limit':3}
    assert result['unpaired'][0]['id']=='g'
    assert result['estimates']['success_difference']['worlds']==2
    assert result['world_cluster_bootstrap_95_ci']==[-1,1]
    old=copy.deepcopy(rows)
    old[0]['metrics']['research_formula_version']='research_metrics_v1'
    mixed=compare_runs(old,[r['id'] for r in old])
    assert any('formula' in r['reason'] for r in mixed['excluded'])


def test_resolved_model_manifest_blobs_and_server_binding(tmp_path,monkeypatch):
    import httpx
    blob=b'Immutable small model artifact fixture, not a real model'
    blob_hash=hashlib.sha256(blob).hexdigest()
    root=tmp_path/'models'
    (root/'blobs').mkdir(parents=True)
    blob_path=root/'blobs'/('sha256-'+blob_hash)
    blob_path.write_bytes(blob)
    path=root/'manifests/registry.ollama.ai/library/mock-model/latest'
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({'schemaVersion':2,'config':{'digest':'sha256:'+blob_hash},
                              'layers':[{'digest':'sha256:'+blob_hash}]}))
    artifact=model_artifact('mock-model',path)
    assert artifact['sha256']==hashlib.sha256(path.read_bytes()).hexdigest()
    assert all(b['sha256']==blob_hash for b in artifact['blobs'])
    blob_path.write_bytes(b'changed')
    with pytest.raises(ValueError,match='differs'):
        model_artifact('mock-model',path)
    class Response:
        def raise_for_status(self):pass
        def json(self):return {'models':[{'name':'mock-model:latest','digest':server_digest[0]}]}
    class Client:
        def __init__(self,**kwargs):pass
        async def __aenter__(self):return self
        async def __aexit__(self,*args):pass
        async def get(self,url):
            assert url.endswith('/api/tags')
            return Response()
        async def post(self,*args,**kwargs):raise AssertionError('No generation authorized')
    monkeypatch.setattr(httpx,'AsyncClient',Client)
    study=Study.__new__(Study)
    study.read=lambda:{'payload':{'model_artifacts':{'mock-model':artifact}}}
    server_digest=[artifact['sha256']]
    asyncio.run(study.check_model_server({'mock-model'}))
    server_digest[0]='0'*64
    with pytest.raises(ValueError,match='differs'):
        asyncio.run(study.check_model_server({'mock-model'}))


def test_plots_are_descriptive_and_software_checks_produce_no_estimate(tmp_path):
    from backend.app.plots import analysis_plots
    result=compare_runs([],[])
    # Empty legacy result is replaced with explicit research analysis for plotting.
    from backend.app.evaluation import compare_research
    result=compare_research([])
    plots=analysis_plots(result,[],'Software qualification')
    assert len(plots)==4 and plots['paired-contrasts.png'].startswith(b'\x89PNG')
    assert b'No eligible paired' in plots['paired-contrasts.svg']
    for name,data in plots.items():(tmp_path/name).write_bytes(data)
