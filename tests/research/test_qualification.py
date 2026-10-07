import asyncio

import pytest
from backend.app.bridge import EngineBridge
from tests.research.helpers import config


@pytest.mark.engine
@pytest.mark.parametrize("recipe,workers,variant,access,change", [
    ("linear_control", 1, "import_enabled", "common_entry", None),
    ("investigate", 2, "source_denied", "matched_split_entry", None),
    ("combine", 4, "ssh_hardened", "matched_split_entry", None),
    ("recover", 2, "import_enabled", "common_entry", "patch_rfi"),
    ("recover", 2, "ssh_hardened", "common_entry", "restore"),
])
def test_isolated_bounded_native_witness_and_architecture_independent_world(tmp_path, recipe, workers, variant, access, change):
    async def check():
        bridge = EngineBridge(tmp_path / "native.log", "enterprise_cc4_research")
        try:
            await bridge.start()
            options = dict(initial_access=access, credential_variant="invalid")
            if change:
                options["change"] = {"mode": change, "response_budget": 1, "response_delay": 4}
            cfg = config(variant, recipe, workers, **options)
            initial = await bridge.call("create", config=cfg)
            report = await bridge.call("qualify", config=cfg)
            assert report["status"] == "native_witness_validated", report
            assert report["ticks"] == report["native_step_count"]
            assert report["final_score"]["mission_success"]
            assert report["world_id"] == initial["world"]["world_id"]
            assert all(a["valid"] and a["outcome"] == "TRUE" for a in report["witness"])
            # Qualification did not consume any tick or capability in the live run.
            live = await bridge.call("step", proposals={})
            assert live["tick"] == 1
            assert not live["views"]["Red_0"]["possessed_tokens"]
            cfg["team"]["architecture"] = "hierarchy"
            again = await bridge.call("create", config=cfg)
            assert again["world"]["world_id"] == initial["world"]["world_id"]
        finally:
            await bridge.close()
    asyncio.run(check())
