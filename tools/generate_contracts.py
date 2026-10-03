"""Generate checked-in JSON Schemas used by UI and API validation."""
import json
from pathlib import Path
from packages.contracts.models import ActionProposal, EpisodeConfig, ExperimentSpec

ROOT = Path(__file__).resolve().parents[1]


def main():
    target = ROOT / "packages/contracts/schemas"
    target.mkdir(parents=True, exist_ok=True)
    for model in [ActionProposal, EpisodeConfig, ExperimentSpec]:
        (target / (model.__name__ + ".json")).write_text(json.dumps(model.model_json_schema(), indent=2) + "\n", encoding="utf-8")
    examples = ROOT / "configs"
    examples.mkdir(exist_ok=True)
    for name, architecture in [("hierarchy", "hierarchy"), ("swarm", "swarm")]:
        config = EpisodeConfig()
        config.team.architecture = architecture
        (examples / (name + ".json")).write_text(config.model_dump_json(indent=2) + "\n", encoding="utf-8")
    (examples / "comparison.json").write_text(ExperimentSpec().model_dump_json(indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
