"""Researcher-only immutable splits and source binding. Never executes a world."""
import copy
import hashlib
import importlib.metadata
import json
import re
import sys
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from backend.app.settings import ROOT
from backend.app.storage import digest, now
from packages.contracts.models import EpisodeConfig, CognitionConfig
from packages.contracts.research_catalog import PUBLIC_CATALOG

VERSION = 'study_freeze_v1'


class WorldReference(BaseModel):
    model_config = ConfigDict(extra='forbid')
    run_id: str = Field(pattern=r'^[a-f0-9]{32}$')
    split: Literal['development', 'validation', 'test']


class FreezeRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    name: str = Field(min_length=1, max_length=120)
    purpose: Literal['software_qualification', 'proposed_study'] = 'software_qualification'
    worlds: list[WorldReference] = Field(min_length=3, max_length=200)
    protocol: dict = Field(default_factory=dict)
    cognitions: list[CognitionConfig] = Field(default_factory=list, max_length=10)
    model_artifacts: dict[str,str] = Field(default_factory=dict)
    episode_treatments: list[EpisodeConfig] = Field(default_factory=list, max_length=50)


def file_hash(path):
    value = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda:handle.read(1024*1024), b''):
            value.update(chunk)
    return value.hexdigest()


def dependency_manifest():
    result = {}
    for name in ('pydantic','fastapi','httpx','uvicorn','matplotlib','numpy'):
        try: result[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError: result[name] = None
    return result


def condition_configuration(config):
    """Frozen public settings; architecture and recorded replicate seeds differ."""
    communication = {k:v for k,v in config['communication'].items() if k!='seed'}
    return {'communication':communication,'claim_ttl':config['team']['claim_ttl'],
            'schedule_mode':config['schedule']['mode']}


def model_artifact(model, path):
    """Resolve an Ollama manifest and its content-addressed local blobs."""
    manifest = json.loads(path.read_text(encoding='utf-8'))
    if manifest.get('schemaVersion')!=2 or not manifest.get('layers') or not manifest.get('config'):
        raise ValueError('Ollama model identity requires its installed manifest, not an arbitrary marker file')
    parent = next((p for p in path.parents if p.name=='manifests'),None)
    if parent is None:
        raise ValueError('Use a manifest inside the installed Ollama models/manifests directory')
    blobs=[]
    for layer in [manifest['config']]+manifest['layers']:
        expected=layer.get('digest','')
        if not re.fullmatch(r'sha256:[a-f0-9]{64}',expected):
            raise ValueError('Invalid content-addressed model blob digest')
        blob=parent.parent/'blobs'/expected.replace(':','-')
        if not blob.is_file() or file_hash(blob)!=expected.split(':')[1]:
            raise ValueError('Installed model blob is missing or differs from its declared content hash')
        blobs.append({'path':str(blob),'sha256':expected.split(':')[1],'size':blob.stat().st_size})
    return {'path':str(path),'sha256':file_hash(path),'blobs':blobs,'model_requested':model}


def source_manifest():
    paths = []
    for folder in ('backend', 'packages', 'prompts', 'engine', 'frontend/src', 'tools'):
        paths.extend(p for p in (ROOT/folder).rglob('*') if p.is_file()
                     and p.suffix in ('.py','.ps1','.txt','.json','.md','.tsx','.ts','.css','.lock'))
    paths.extend(p for p in (ROOT/'pyproject.toml',ROOT/'frontend/package-lock.json') if p.exists())
    return {p.relative_to(ROOT).as_posix():file_hash(p) for p in sorted(set(paths))}


def world_configuration(config):
    """Identity of materialization; treatment/scheduler/transport stay separate."""
    return {'scenario': config['scenario'], 'workers': config['team']['workers'],
            'horizon': config['schedule']['max_ticks'], 'resources': config['resources']}


def causal_world(snapshot, config):
    """Ignore addresses, opaque IDs and native actor count; retain causal placement.

    This deliberately conservative equivalence prevents renamed CC4 networks from
    being counted as independent networks. It is specific to the finite v1 recipes.
    """
    truth = snapshot['research_truth']
    token_semantics = truth['tokens']
    artifacts = {}
    for host, notes in truth['artifacts'].items():
        clean = []
        for note in notes:
            public = copy.deepcopy(note['public'])
            public.pop('artifact_id', None)
            if 'token_ref' in public:
                public['token'] = copy.deepcopy(token_semantics[public.pop('token_ref')])
            for lead in [public.get('lead')] + public.get('leads', []):
                if lead:
                    lead.pop('address', None)
            clean.append({'read':note['read'],'public':public})
        artifacts[host] = clean
    return {'version':VERSION, 'recipe':truth['recipe'], 'roles':truth['roles'],
            'variant':truth['variant'], 'artifacts':artifacts,
            'source_permissions':snapshot['route_manifest']['rules'],
            'change':config['scenario']['research']['change'],
            'initial_access':config['scenario']['research']['initial_access'],
            'targets':sorted(config['scenario']['targets'])}


class Study:
    def __init__(self, store, study_id):
        if not re.fullmatch(r'[a-f0-9]{32}', study_id):
            raise ValueError('Invalid study ID')
        self.store, self.id = store, study_id
        self.directory = store.root/'studies'/study_id
        self.path = self.directory/'freeze.json'

    @classmethod
    def create(cls, store, request):
        request = FreezeRequest.model_validate(request)
        worlds, split_keys = [], {}
        models = {}
        for model, location in request.model_artifacts.items():
            path = Path(location).resolve(strict=True)
            if not path.is_file():
                raise ValueError('Model identity must reference a local immutable artifact file')
            models[model] = model_artifact(model,path)
        for reference in request.worlds:
            directory = store.path(reference.run_id)
            config = EpisodeConfig.model_validate_json((directory/'config.json').read_text(encoding='utf-8')).model_dump()
            meta = store.get(reference.run_id)
            from backend.app.runs import source_fingerprint
            if meta.get('code_fingerprint')!=source_fingerprint():
                raise ValueError('World was qualified under different source; initialize and qualify it with current source before freezing')
            if meta.get('feasibility_status')!='native_witness_validated' or config['scenario']['profile']!='enterprise_cc4_research':
                raise ValueError('Every frozen world requires a validated native research witness')
            qualification = json.loads((directory/'qualification.json').read_text(encoding='utf-8'))
            if qualification['status']!='native_witness_validated':
                raise ValueError('Qualification artifact contradicts metadata')
            if config['cognition']['provider']!='scripted' and config['cognition']['model'] not in models:
                raise ValueError('Live model freezes require a resolved model artifact digest; requested model names alone are insufficient')
            world = json.loads((directory/'world.json').read_text(encoding='utf-8'))
            causal = causal_world(world['snapshot'],config)
            causal_hash = digest(causal)
            if causal_hash in split_keys and split_keys[causal_hash]!=reference.split:
                raise ValueError('Split leakage: same causal combination/placement; changing IPs or opaque identifiers is not a holdout')
            split_keys[causal_hash] = reference.split
            versions = json.loads((directory/'manifest.json').read_text(encoding='utf-8'))['versions']
            worlds.append({'source_run_id':reference.run_id,'split':reference.split,
                'materialization_key':digest(world_configuration(config)), 'causal_world_hash':causal_hash,
                'technical_world_hash':digest(world), 'causal_world':causal, 'config':config,
                'world':world,'qualification':qualification,'engine_versions':versions,
                'source_run_fingerprint':meta['code_fingerprint']})
        if {w['split'] for w in worlds}!={'development','validation','test'}:
            raise ValueError('Development, validation and test worlds must all be declared')
        # The test split must combine known rule components, not introduce a new
        # undocumented technique. Placement/condition combinations are withheld.
        earlier = [w['causal_world'] for w in worlds if w['split']!='test']
        for world in (w['causal_world'] for w in worlds if w['split']=='test'):
            for field in ('recipe','variant','initial_access','change'):
                if not any(old[field]==world[field] for old in earlier):
                    raise ValueError('Test introduces an unqualified rule component: '+field)
            for role, host in world['roles'].items():
                if not any(old['roles'].get(role)==host for old in earlier):
                    raise ValueError('Test introduces an unseen role placement: '+role)
        if request.purpose=='proposed_study':
            required = {'primary_endpoint','contrasts','exclusions','retry_rule','sample_size_rationale','development_pilot_reference'}
            if not required<=request.protocol.keys() or any(not request.protocol[k] for k in required):
                raise ValueError('A proposed study needs the complete predeclared protocol and an authorized pilot reference')
        sources = source_manifest()
        cognitions = list({digest(c):c for c in [w['config']['cognition'] for w in worlds]+[c.model_dump() for c in request.cognitions]}.values())
        for cognition in cognitions:
            if cognition['provider']!='scripted' and cognition['model'] not in models:
                raise ValueError('Declared model treatments require local model artifact hashes')
        treatments = [w['config'] for w in worlds]+[c.model_dump() for c in request.episode_treatments]
        for treatment in treatments:
            if not any(digest(world_configuration(treatment))==w['materialization_key'] for w in worlds):
                raise ValueError('Every declared episode treatment requires an already qualified materialized world')
        conditions = list({digest(condition_configuration(c)):condition_configuration(c) for c in treatments}.values())
        payload = {'version':VERSION,'name':request.name,'purpose':request.purpose,
            'protocol':request.protocol,'sources':sources,'source_hash':digest(sources),
            'catalog_hash':digest(PUBLIC_CATALOG),'worlds':worlds,'cognitions':cognitions,'model_artifacts':models,
            'conditions':conditions,'service_dependencies':dependency_manifest(),
            'service_python':sys.version,
            'limitations':['Finite fixed CC4 scaffold; causal equivalence is conservative.',
                'No study or model is executed by freezing. Live-model identity qualification remains outstanding.']}
        identity = digest(payload)[:32]
        study = cls(store,identity)
        if not study.path.exists():
            store.write_json(study.path, {'id':identity,'created_at':now(),'payload':payload,'payload_hash':digest(payload)})
            for name, expected in sources.items():
                data=(ROOT/name).read_bytes()
                if hashlib.sha256(data).hexdigest()!=expected:
                    raise ValueError('Source changed while creating the freeze')
                destination=study.directory/'source'/name
                destination.parent.mkdir(parents=True,exist_ok=True)
                destination.write_bytes(data)
        return study

    def read(self):
        document = json.loads(self.path.read_text(encoding='utf-8'))
        if digest(document['payload'])!=document['payload_hash'] or document['payload_hash'][:32]!=self.id:
            raise ValueError('Freeze artifact changed; immutable hash check failed')
        return document

    def check_sources(self):
        document = self.read()
        if source_manifest()!=document['payload']['sources']:
            raise ValueError('Source/prompt/catalog/dependency declarations changed after freeze; create a new freeze')
        dependencies = dependency_manifest()
        if dependencies!=document['payload']['service_dependencies']:
            raise ValueError('Service dependencies changed after freeze')
        if document['payload'].get('service_python') and document['payload']['service_python']!=sys.version:
            raise ValueError('Service Python runtime changed after freeze')
        for artifact in document['payload']['model_artifacts'].values():
            if file_hash(Path(artifact['path']))!=artifact['sha256']:
                raise ValueError('Declared model artifact changed after freeze')
            for blob in artifact.get('blobs',[]):
                if file_hash(Path(blob['path']))!=blob['sha256']:
                    raise ValueError('Declared model weights changed after freeze')
        return document

    async def check_model_server(self, models):
        """Read local metadata only, before any frozen live episode is constructed."""
        import os
        import httpx
        from urllib.parse import urlparse
        endpoint=os.environ.get('OLLAMA_URL','http://127.0.0.1:11434').rstrip('/')
        parsed=urlparse(endpoint)
        if parsed.scheme!='http' or parsed.hostname not in ('localhost','127.0.0.1','::1'):
            raise ValueError('Frozen local-model checks require a loopback HTTP server')
        expected=self.read()['payload']['model_artifacts']
        async with httpx.AsyncClient(timeout=15) as client:
            response=await client.get(endpoint+'/api/tags')
            response.raise_for_status()
            actual={m['name']:m['digest'] for m in response.json()['models']}
        for model in models:
            name=model if ':' in model else model+':latest'
            if actual.get(name)!=expected[model]['sha256']:
                raise ValueError('Local server model tag differs from the frozen installed manifest: '+model)

    def bind(self, config, split):
        document = self.check_sources()
        key = digest(world_configuration(config))
        matches = [w for w in document['payload']['worlds'] if w['materialization_key']==key and w['split']==split]
        if not matches:
            raise ValueError('Job is not a member of the frozen materialized split')
        selected = matches[0]
        if config['cognition'] not in document['payload']['cognitions']:
            raise ValueError('Policy/model/settings differ from the frozen world treatment')
        if condition_configuration(config) not in document['payload'].get('conditions',[]):
            raise ValueError('Transport/claim/action-capacity settings were not frozen; declare an episode treatment')
        return selected
