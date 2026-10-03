"""Configuration/replay helpers. Experiments require explicit future execution."""
import argparse
import asyncio
import json
from pathlib import Path
from backend.app.evaluation import expand
from backend.app.runs import RunManager
from backend.app.settings import DATA_ROOT, ROOT
from backend.app.storage import Store
from packages.contracts.models import EpisodeConfig, ExperimentSpec


def main():
    parser = argparse.ArgumentParser(description="AbstractCyberSim research workbench")
    commands = parser.add_subparsers(dest="command", required=True)
    server = commands.add_parser("serve", help="Open the local workbench; starts no simulation")
    server.add_argument("--port", type=int, default=8787)
    for name in ["validate", "preview"]:
        p = commands.add_parser(name)
        p.add_argument("config", type=Path)
    p = commands.add_parser("initialize", help="Create a paused world without taking any actions")
    p.add_argument("config", type=Path)
    commands.add_parser("list")
    p = commands.add_parser("metrics")
    p.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.command == "serve":
        import uvicorn
        uvicorn.run("backend.app.api:app", host="127.0.0.1", port=args.port)
    elif args.command in ["validate", "preview"]:
        data = json.loads(args.config.read_text(encoding="utf-8-sig"))
        result = EpisodeConfig.model_validate(data).model_dump() if args.command == "validate" else expand(ExperimentSpec.model_validate(data))
        print(json.dumps(result, indent=2))
    elif args.command == "initialize":
        async def initialize():
            store = Store(DATA_ROOT)
            manager = RunManager(store)
            try:
                print(json.dumps(await manager.create(EpisodeConfig.model_validate_json(args.config.read_text(encoding="utf-8-sig"))), indent=2))
            finally:
                await manager.close()
        asyncio.run(initialize())
    elif args.command == "list":
        print(json.dumps(Store(DATA_ROOT).list(), indent=2))
    elif args.command == "metrics":
        args.output.write_text(Store(DATA_ROOT).csv(), encoding="utf-8")


if __name__ == "__main__":
    main()
