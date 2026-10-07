"""Local researcher API. Creating a run initializes it; only explicit controls step."""
import asyncio
import io
import json
import zipfile
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field
from backend.app.evaluation import compare_runs, expand
from backend.app.runs import RunManager
from backend.app.settings import DATA_ROOT, ROOT, engine_python
from backend.app.storage import Store
from packages.contracts.models import EpisodeConfig, ExperimentSpec, StepRequest, ENGINE_COMMIT
from packages.contracts.capabilities import profiles
from backend.app.baselines import describe_policy
from backend.app.batches import Batch
from backend.app.studies import Study, FreezeRequest


class CompareRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    run_ids: list[str] = Field(min_length=2, max_length=10000)


class BatchExecution(BaseModel):
    model_config = ConfigDict(extra='forbid')
    confirm_execution: bool = False
    max_jobs: int = Field(default=1, ge=1, le=10000)
    technical_retries: int = Field(default=0, ge=0, le=2)


def create_app(data_root: Path = DATA_ROOT):
    store = Store(data_root)
    manager = RunManager(store)
    batch_tasks = {}

    @asynccontextmanager
    async def lifespan(app):
        store.recover()
        yield
        for batch_id, task in batch_tasks.items():
            if not task.done():
                Batch(store, batch_id).request_stop()
        await asyncio.gather(*batch_tasks.values(), return_exceptions=True)
        await manager.close()

    app = FastAPI(title="AbstractCyberSim Workbench", version="0.1.0", lifespan=lifespan)
    app.state.store, app.state.manager = store, manager

    @app.exception_handler(KeyError)
    async def missing(request, exc):
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=404, content={"detail": str(exc.args[0])})

    @app.exception_handler(ValueError)
    async def invalid(request, exc):
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(RuntimeError)
    async def runtime(request, exc):
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=503, content={"detail": str(exc)})

    @app.middleware("http")
    async def local_origin(request: Request, call_next):
        # A local app has no external account/authentication flow. Restrict
        # mutating browser requests to this origin; no permissive CORS wildcard.
        if request.method not in ["GET", "HEAD", "OPTIONS"]:
            origin = request.headers.get("origin")
            allowed = {f"http://{host}:{port}" for host in ["127.0.0.1", "localhost"] for port in [request.url.port or 80, 5173]}
            if origin and origin not in allowed:
                from fastapi.responses import JSONResponse
                return JSONResponse(status_code=403, content={"detail": "Local workbench origin required"})
        return await call_next(request)

    @app.get("/api/capabilities")
    async def capabilities():
        try:
            interpreter, setup_error = engine_python(), None
        except RuntimeError as exc:
            interpreter, setup_error = None, str(exc)
        available = profiles()
        for profile in available:
            try:
                engine_python(profile["id"])
                profile.update(engine_interpreter_available=True, setup_error=None)
            except RuntimeError as exc:
                profile.update(engine_interpreter_available=False, setup_error=str(exc))
        return {"version": "0.2.0", "schema_version": "1.0", "engine_commit": ENGINE_COMMIT, "engine_interpreter_available": bool(interpreter), "setup_error": setup_error, "profiles": available, "architectures": ["hierarchy", "swarm", "independent"], "providers": ["scripted", "ollama"], "scripted_policies": [describe_policy(n) for n in ["legacy", "local_rules", "local_replan", "local_search", "fixed_workflow", "evidence_controller", "observed_planner"]], "default_config": EpisodeConfig().model_dump(), "episode_schema": EpisodeConfig.model_json_schema(), "experiment_schema": ExperimentSpec.model_json_schema(), "auto_runs": False, "unsupported": ["arbitrary zone topology", "real authentication or security testing", "benign-user/phishing qualification", "Impact mission", "arbitrary engine checkpoint resume", "hosted LLM adapters"]}

    @app.get("/api/runs")
    async def list_runs():
        return store.list()

    @app.post("/api/configs/validate")
    async def validate_config(config: EpisodeConfig):
        return config.model_dump()

    @app.post("/api/runs", status_code=201)
    async def create_run(config: EpisodeConfig):
        return await manager.create(config)

    @app.get("/api/runs/{run_id}")
    async def get_run(run_id: str):
        return store.get(run_id)

    @app.get("/api/runs/{run_id}/config")
    async def config(run_id: str):
        store.get(run_id)
        return json.loads((store.path(run_id) / "config.json").read_text(encoding="utf-8"))

    @app.get("/api/runs/{run_id}/frame")
    async def frame(run_id: str, tick: int | None = Query(default=None, ge=0)):
        return store.frame(run_id, tick)

    @app.get("/api/runs/{run_id}/events")
    async def events(run_id: str, after: int = Query(default=0, ge=0)):
        return store.events(run_id, after)

    @app.post("/api/runs/{run_id}/step")
    async def step(run_id: str, request: StepRequest):
        run = manager.get(run_id)
        if run.meta["status"] == "running":
            raise ValueError("Pause before stepping or entering manual actions")
        return await run.advance({a: p.model_dump() for a, p in request.overrides.items()})

    @app.post("/api/runs/{run_id}/control/{command}")
    async def control(run_id: str, command: str):
        run = manager.get(run_id)
        if command == "start":
            return run.start()
        if command == "pause":
            return await run.pause()
        if command == "stop":
            return await run.stop()
        raise HTTPException(404, "Unknown control command")

    @app.get("/api/runs/{run_id}/qualification")
    async def qualification(run_id: str):
        store.get(run_id)
        path = store.path(run_id) / "qualification.json"
        if not path.is_file():
            raise HTTPException(404, "This historical profile has no research feasibility artifact")
        return json.loads(path.read_text(encoding="utf-8"))

    @app.get("/api/runs/{run_id}/export")
    async def export_run(run_id: str):
        store.get(run_id)
        run = manager.live.get(run_id)
        if run and run.meta["status"] == "running":
            raise ValueError("Pause the run before exporting a consistent evidence bundle")
        content = io.BytesIO()
        directory = store.path(run_id)
        with zipfile.ZipFile(content, "w", zipfile.ZIP_DEFLATED) as archive:
            for file in sorted(directory.rglob("*")):
                if file.is_file() and file.suffix != ".tmp":
                    archive.write(file, arcname=str(file.relative_to(directory)))
        return Response(content.getvalue(), media_type="application/zip", headers={"Content-Disposition": f'attachment; filename="run-{run_id}.zip"'})

    @app.get("/api/export/metrics.csv")
    async def csv():
        return Response(store.csv(), media_type="text/csv", headers={"Content-Disposition": 'attachment; filename="research-metrics.csv"'})

    @app.post("/api/experiments/preview")
    async def preview(spec: ExperimentSpec):
        return expand(spec)

    @app.post('/api/experiments/prepare-pilot')
    async def prepare_pilot(spec: ExperimentSpec):
        from backend.app.preparation import prepare_pilot as prepare
        return prepare(spec)

    @app.post('/api/batches', status_code=201)
    async def save_batch(spec: ExperimentSpec, freeze_id: str | None = None, split: str | None = None):
        return Batch.create(store, expand(spec), freeze_id=freeze_id, split=split).read()

    @app.get('/api/batches/{batch_id}')
    async def read_batch(batch_id: str):
        return Batch(store, batch_id).read()

    @app.post('/api/studies', status_code=201)
    async def freeze_study(request: FreezeRequest):
        return Study.create(store,request).read()

    @app.get('/api/studies')
    async def list_studies():
        entries = []
        for path in sorted((store.root/'studies').glob('*/freeze.json')):
            document = Study(store,path.parent.name).read()
            entries.append({'id':document['id'],'name':document['payload']['name'],
                            'purpose':document['payload']['purpose'],'worlds':len(document['payload']['worlds'])})
        return entries

    @app.get('/api/studies/{study_id}')
    async def read_study(study_id: str):
        return Study(store,study_id).read()

    @app.get('/api/studies/{study_id}/export')
    async def export_frozen_study(study_id: str):
        from backend.app.exports import export_study
        output=store.root/'studies'/study_id/'exports'/'study.zip'
        result=export_study(store,study_id,output)
        return FileResponse(result['path'],media_type='application/zip',filename='study-'+study_id+'.zip')

    @app.post('/api/batches/{batch_id}/stop')
    async def stop_batch(batch_id: str):
        batch = Batch(store, batch_id)
        batch.request_stop()
        return {'id':batch_id,'stop_requested':True}

    @app.post('/api/batches/{batch_id}/execute')
    async def execute_batch(batch_id: str, request: BatchExecution):
        if not request.confirm_execution:
            raise ValueError('Explicit execution confirmation is required; saving and previewing are idle')
        batch = Batch(store, batch_id)
        state = batch.read()
        if any(j['config']['cognition']['provider']!='scripted' for j in state['jobs']):
            raise ValueError('This UI executor is scripted only; live execution needs separate authorization')
        if batch_id in batch_tasks and not batch_tasks[batch_id].done():
            raise ValueError('This queue is already running')
        task = asyncio.create_task(batch.execute(max_jobs=request.max_jobs, technical_retries=request.technical_retries))
        # Consume exceptions for persistent-state inspection rather than losing
        # them as unhandled background-task warnings.
        task.add_done_callback(lambda finished: finished.exception() if not finished.cancelled() else None)
        batch_tasks[batch_id] = task
        return {'id':batch_id,'status':'running','max_jobs':request.max_jobs}

    @app.post("/api/analysis/compare")
    async def compare(request: CompareRequest):
        return compare_runs(store.list(), request.run_ids)

    @app.get("/api/health")
    async def health():
        return {"status": "ok", "experiments_started_automatically": False}

    distribution = ROOT / "frontend/dist"
    if distribution.is_dir():
        app.mount("/assets", StaticFiles(directory=distribution / "assets"), name="assets")

        @app.get("/")
        async def index():
            return FileResponse(distribution / "index.html")
    return app


app = create_app()
