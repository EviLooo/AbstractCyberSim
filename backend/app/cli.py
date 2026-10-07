"""Configuration/replay helpers. Experiments require explicit future execution."""
import argparse
import asyncio
import json
from pathlib import Path
from backend.app.evaluation import expand
from backend.app.evaluation import metrics
from backend.app.batches import Batch
import httpx
from backend.app.settings import DATA_ROOT
from backend.app.storage import Store
from packages.contracts.models import EpisodeConfig, ExperimentSpec, StepRequest
from backend.app.diagnostics import reduce_decisions


def arguments(argv=None):
    parser = argparse.ArgumentParser(description="AbstractCyberSim research workbench")
    commands = parser.add_subparsers(dest="command", required=True)
    server = commands.add_parser("serve", help="Open the local workbench; starts no simulation")
    server.add_argument("--port", type=int, default=8787)
    for name in ["validate", "preview", "prepare-pilot"]:
        p = commands.add_parser(name)
        p.add_argument("config", type=Path)
    p = commands.add_parser("initialize", help="Create a paused world without taking any actions")
    p.add_argument("config", type=Path)
    p.add_argument("--port", type=int, default=8787)
    p = commands.add_parser("step", help="Submit one joint tick through the running local service")
    p.add_argument("run_id")
    p.add_argument("--overrides", type=Path, help="Exploration-only StepRequest JSON file")
    p.add_argument("--port", type=int, default=8787)
    p = commands.add_parser("control", help="Start, pause, continue, or stop a live environment")
    p.add_argument("run_id")
    p.add_argument("action", choices=["start", "continue", "pause", "stop"])
    p.add_argument("--port", type=int, default=8787)
    for name in ["frame", "events"]:
        p = commands.add_parser(name, help="Read saved evidence without advancing the engine")
        p.add_argument("run_id")
        p.add_argument("--port", type=int, default=8787)
        p.add_argument("--tick" if name == "frame" else "--after", type=int, default=None if name == "frame" else 0)
    commands.add_parser("list")
    p = commands.add_parser("diagnostics", help="Recompute saved behavior offline; starts no engine or model")
    p.add_argument("run_id")
    p = commands.add_parser("metrics")
    p.add_argument("output", type=Path)
    p = commands.add_parser("recompute", help="Reduce saved frames offline without an engine or provider")
    p.add_argument("run_id")
    p.add_argument("--output", type=Path)
    p = commands.add_parser('batch-create', help='Save a validated queue; starts no episodes')
    p.add_argument('spec', type=Path)
    p.add_argument('--freeze')
    p.add_argument('--split', choices=['development','validation','test'])
    p = commands.add_parser('study-freeze', help='Freeze existing qualified worlds and source; starts no episodes')
    p.add_argument('manifest', type=Path)
    p = commands.add_parser('study-check', help='Verify immutable freeze and current source, without execution')
    p.add_argument('study_id')
    p = commands.add_parser('study-export', help='Export saved frozen evidence/analysis offline; no execution')
    p.add_argument('study_id')
    p.add_argument('output',type=Path)
    p = commands.add_parser('batch-run', help='Explicit sequential execution or scheduling resume')
    p.add_argument('batch_id')
    p.add_argument('--execute', action='store_true')
    p.add_argument('--max-jobs', type=int, default=1)
    p.add_argument('--technical-retries', type=int, default=0)
    p.add_argument('--allow-live', action='store_true')
    p = commands.add_parser('batch-stop', help='Stop scheduling at the next native boundary')
    p.add_argument('batch_id')
    return parser.parse_args(argv)


async def remote(args, client):
    if args.command == "initialize":
        config = EpisodeConfig.model_validate_json(args.config.read_text(encoding="utf-8-sig"))
        response = await client.post("/api/runs", json=config.model_dump())
    elif args.command == "step":
        body = StepRequest.model_validate_json(args.overrides.read_text(encoding="utf-8-sig")) if args.overrides else StepRequest()
        response = await client.post(f"/api/runs/{args.run_id}/step", json=body.model_dump())
    elif args.command == "control":
        command = "start" if args.action == "continue" else args.action
        response = await client.post(f"/api/runs/{args.run_id}/control/{command}")
    else:
        params = {"tick": args.tick} if args.command == "frame" and args.tick is not None else {"after": args.after} if args.command == "events" else {}
        response = await client.get(f"/api/runs/{args.run_id}/{args.command}", params=params)
    response.raise_for_status()
    return response.json()


def main():
    args = arguments()
    if args.command == "serve":
        import uvicorn
        uvicorn.run("backend.app.api:app", host="127.0.0.1", port=args.port)
    elif args.command in ["validate", "preview", "prepare-pilot"]:
        data = json.loads(args.config.read_text(encoding="utf-8-sig"))
        if args.command == 'prepare-pilot':
            from backend.app.preparation import prepare_pilot
            result = prepare_pilot(ExperimentSpec.model_validate(data))
        else:
            result = EpisodeConfig.model_validate(data).model_dump() if args.command == "validate" else expand(ExperimentSpec.model_validate(data))
        print(json.dumps(result, indent=2))
    elif args.command in ["initialize", "step", "control", "frame", "events"]:
        async def request():
            async with httpx.AsyncClient(base_url=f"http://127.0.0.1:{args.port}", timeout=120) as client:
                return await remote(args, client)
        print(json.dumps(asyncio.run(request()), indent=2))
    elif args.command == "list":
        print(json.dumps(Store(DATA_ROOT).list(), indent=2))
    elif args.command == "diagnostics":
        store = Store(DATA_ROOT)
        meta = store.get(args.run_id)
        frames = [store.frame(args.run_id, tick) for tick in range(meta["tick"] + 1)]
        print(json.dumps({"structure": frames[-1].get("diagnostics", {}).get("structure"),
                          "behavior": reduce_decisions(frames)}, indent=2))
    elif args.command == "metrics":
        args.output.write_text(Store(DATA_ROOT).csv(), encoding="utf-8")
    elif args.command == "recompute":
        store = Store(DATA_ROOT)
        meta = store.get(args.run_id)
        config = EpisodeConfig.model_validate_json((store.path(args.run_id)/'config.json').read_text(encoding='utf-8'))
        frames = [store.frame(args.run_id, tick) for tick in range(meta['tick']+1)]
        usage_keys = ('provider','scripted_policy','calls','charged_tokens','unknown_usage_calls','provider_failures','provider_refusals','prompt_hashes','is_llm','per_actor_usage')
        usage = {k: meta.get('metrics', {}).get(k, frames[-1]['cognition'].get(k)) for k in usage_keys}
        result = metrics(frames, usage, config.schedule.max_ticks, meta.get('termination_reason'))
        if args.output:
            store.write_json(args.output, result)
        else:
            print(json.dumps(result, indent=2))
    elif args.command == 'batch-create':
        spec = ExperimentSpec.model_validate_json(args.spec.read_text(encoding='utf-8-sig'))
        batch = Batch.create(Store(DATA_ROOT), expand(spec),freeze_id=args.freeze,split=args.split)
        print(json.dumps(batch.read(), indent=2))
    elif args.command == 'batch-stop':
        Batch(Store(DATA_ROOT), args.batch_id).request_stop()
        print('Stop requested; unfinished native episodes will be retained as partial attempts.')
    elif args.command in ('study-freeze','study-check'):
        from backend.app.studies import Study
        store = Store(DATA_ROOT)
        result = Study.create(store,json.loads(args.manifest.read_text(encoding='utf-8-sig'))).read() if args.command=='study-freeze' else Study(store,args.study_id).check_sources()
        print(json.dumps(result,indent=2))
    elif args.command=='study-export':
        from backend.app.exports import export_study
        print(json.dumps(export_study(Store(DATA_ROOT),args.study_id,args.output),indent=2))
    elif args.command == 'batch-run':
        batch = Batch(Store(DATA_ROOT), args.batch_id)
        result = asyncio.run(batch.execute(max_jobs=args.max_jobs, technical_retries=args.technical_retries,
                                          allow_live=args.allow_live)) if args.execute else batch.read()
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
