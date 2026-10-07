import asyncio
import copy

import pytest
from pydantic import ValidationError
from backend.app.bridge import EngineBridge
from packages.contracts.models import ActionProposal, EpisodeConfig
from tests.research.helpers import config, finish, ip, action, evidence, TARGET_A


def test_strict_research_contracts_preserve_old_version():
    assert EpisodeConfig().schema_version == "1.0"
    assert EpisodeConfig.model_validate(config()).schema_version == "2.0"
    for change in [{"schema_version": "1.0"}, {"team": {"workers": 3}},
                   {"communication": {"extra_delay": 1}}]:
        cfg = config()
        cfg.update(change)
        with pytest.raises(ValidationError):
            EpisodeConfig.model_validate(cfg)
    for proposal in [{"action": "AttemptAccess", "target": "x"},
                     {"action": "Probe", "target": "x", "probe": "auth_policy", "port": 80},
                     {"action": "Sleep", "method": "web_rfi"},
                     {"action": "AttemptAccess", "target": "x", "method": "credential_login"}]:
        with pytest.raises(ValidationError):
            ActionProposal.model_validate(proposal)


@pytest.mark.engine
def test_identical_initial_inputs_different_informative_probes_and_persistent_retries(tmp_path):
    async def check():
        bridge = EngineBridge(tmp_path / "native.log", "enterprise_cc4_research")
        try:
            hello = await bridge.start()
            assert not hello["upstream_dirty"]
            results = []
            for variant in ("import_enabled", "import_disabled", "source_denied"):
                initial = await bridge.call("create", config=config(variant))
                target = ip(initial, TARGET_A)
                entry = initial["views"]["Red_0"]["sessions"][0]["hostname"]
                inspected = await finish(bridge, {"action": "InspectArtifacts", "target": entry})
                assert target in inspected["views"]["Red_0"]["known"]["ip_address"]
                connectivity = await finish(bridge, {"action": "Probe", "target": target,
                                                   "probe": "connectivity", "port": 80})
                feature = await finish(bridge, {"action": "Probe", "target": target,
                                               "probe": "service_behavior", "port": 80})
                scanned = await finish(bridge, {"action": "DiscoverNetworkServices", "target": target})
                retries = []
                if variant != "source_denied":
                    for _ in range(3):
                        attempted = await finish(bridge, {"action": "AttemptAccess", "method": "web_rfi", "target": target})
                        retries.append(action(attempted)["outcome"])
                        assert evidence(attempted)[0]["response"] == ("access_established" if variant == "import_enabled" else "access_not_established")
                results.append((initial, evidence(connectivity), evidence(feature), retries))
            for other in results[1:]:
                assert other[0]["views"] == results[0][0]["views"]
                assert other[0]["observations"] == results[0][0]["observations"]
            assert results[0][1][0]["response"] == results[1][1][0]["response"] == "tcp_handshake"
            assert results[2][1][0]["response"] == "timeout"
            assert [r[2][0]["response"] for r in results] == ["external_import_accepted", "external_import_refused", "timeout"]
            assert results[0][3] == ["TRUE"] * 3
            assert results[1][3] == ["FALSE"] * 3
        finally:
            await bridge.close()
    asyncio.run(check())
