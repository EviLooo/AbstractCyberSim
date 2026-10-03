"""Configuration/replay helpers. Experiments require explicit future execution."""
import argparse
import asyncio
import json
from pathlib import Path
from backend.app.evaluation import expand
import httpx
from backend.app.settings import DATA_ROOT
from backend.app.storage import Store
from packages.contracts.models import EpisodeConfig, ExperimentSpec, StepRequest


def arguments(argv=None):
    parser = argparse.ArgumentParser(description="AbstractCyberSim research workbench")
    commands = parser.add_subparsers(dest="command", required=True)
    server = commands.add_parser("serve", help="Open the local workbench; starts no simulation")
    server.add_argument("--port", type=int, default=8787)
    for name in ["validate", "preview"]:
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
    p = commands.add_parser("metrics")
    p.add_argument("output", type=Path)
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
    elif args.command in ["validate", "preview"]:
        data = json.loads(args.config.read_text(encoding="utf-8-sig"))
        result = EpisodeConfig.model_validate(data).model_dump() if args.command == "validate" else expand(ExperimentSpec.model_validate(data))
        print(json.dumps(result, indent=2))
    elif args.command in ["initialize", "step", "control", "frame", "events"]:
        async def request():
            async with httpx.AsyncClient(base_url=f"http://127.0.0.1:{args.port}", timeout=120) as client:
                return await remote(args, client)
        print(json.dumps(asyncio.run(request()), indent=2))
    elif args.command == "list":
        print(json.dumps(Store(DATA_ROOT).list(), indent=2))
    elif args.command == "metrics":
        args.output.write_text(Store(DATA_ROOT).csv(), encoding="utf-8")


if __name__ == "__main__":
    main()
