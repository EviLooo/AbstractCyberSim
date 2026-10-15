"""Isolate native prerequisites in an engine-only subprocess, never user data."""
import json
import subprocess

import pytest

from backend.app.settings import ROOT, engine_python
from packages.contracts.models import EpisodeConfig


@pytest.mark.engine
def test_native_route_ownership_and_privileged_mission_boundaries():
    config = EpisodeConfig()
    config.team.workers = 2
    config.scenario.targets = ["User1"]
    result = subprocess.run(
        [engine_python(), "-m", "tests.native_boundary_fixture"],
        input=json.dumps(config.model_dump()), cwd=ROOT,
        capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, result.stderr
    checks = json.loads(result.stdout)["checks"]
    assert len(checks) == 10 and len(set(checks)) == 10
