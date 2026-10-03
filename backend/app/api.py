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


class CompareRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    run_ids: list[str] = Field(min_length=2, max_length=10000)


def create_app(data_root: Path = DATA_ROOT):
    store = Store(data_root)
    manager = RunManager(store)

    @asynccontextmanager
    async def lifespan(app):
        store.recover()
        yield
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
        return {"version": "0.1.0", "schema_version": "1.0", "engine_commit": ENGINE_COMMIT, "engine_interpreter_available": bool(interpreter), "setup_error": setup_error, "profiles": [{"id": "enterprise_legacy", "name": "Enterprise · CybORG Scenario2", "subnets": 3, "hosts": 13, "qualification": "Software integration; research calibration pending"}], "architectures": ["hierarchy", "swarm", "independent"], "providers": ["scripted", "ollama"], "default_config": EpisodeConfig().model_dump(), "episode_schema": EpisodeConfig.model_json_schema(), "experiment_schema": ExperimentSpec.model_json_schema(), "auto_runs": False, "unsupported": ["qualified four-zone scenarios", "active recovery defender", "Impact mission", "arbitrary engine checkpoint resume", "hosted LLM adapters"]}

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
