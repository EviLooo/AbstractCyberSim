# Implemented layers and safe extension points

The required application is one local repository. Preserve the historical Mesa/
legacy profiles. The investigative schema2 profile uses an isolated pinned CC4
process; it does not require cloud infrastructure or operational security tooling.

| Layer | Files | Responsibility / extension rule |
| --- | --- | --- |
| Validated configuration | packages/contracts/models, research_profile, research_catalog | Version public mechanics and reject unsupported combinations; regenerate schemas/types deliberately |
| Materialized model | packages/engine_worker/cc4/research/{compiler,state,actions,changes,evidence,runtime} | Native owned sessions, persistent conditions, local artifacts and scoped simulated references; custom actions only mutate simulator state |
| Engine boundary | backend/app/bridge; packages/engine_worker/main | One joint step per tick, separate engine Python; never import native engine into UI/service policies |
| Private perception | backend/app/{knowledge,beliefs,research_agents}.py | Delayed recipient evidence, source-bound mechanical candidates, original timestamps; never filter using hidden compatibility |
| Organizations | policies and runs | Delivered-only sessionless leader or local peer claims; common gateway and attempt/action budgets |
| Cognition | providers, research_policy, prompts | Scripted controls/structured local provider; public priors, repair/cancellation/accounting, no fallback that silently supplies a successful strategy |
| Research tooling | evaluation, research_metrics, batches, studies, exports, plots, preparation | Event-based versioned reducers, fresh retry attempts, immutable splits/source and offline artifacts |
| UI | frontend/src, projection modules | Configure a new run, explicit controls, observed/private graphs and honest privileged truth, immutable replay/export |
| Verification | tests/research; audit docs | Bounded native/software/mock/UI checks; software fixtures never scientific data |

Change a policy's heuristics in code; name/version/freeze it. Adjust supported
difficulty dimensions in config (conditions, entry, delay, shared response,
hold/deadline, budgets and capacity). Add a new causal mechanism in engine code,
its public rule/strict contract/private evidence, native positive/negative witness,
paired-input test, UI projection and metric/review description. Do not implement
new semantics solely as a UI animation or grant capability through messages.

No agent operation scans/authenticates to/exploits a real system. Host addresses,
ports and tokens are simulation fields. Only the optional local model HTTP API and
local workbench communicate with processes; no attack payloads are part of the
model. Avoid introducing real-target adapters into this project scope.

Tests to select by change: contracts/public policy unit checks; relevant native
mechanism/source/organization fixture; projection test and actual browser for UI;
offline hand counts/hash checks for metrics/export. Stop after appropriate checks
pass unless a new failure/change justifies more. Use the requirement ledger and
execution Goal gate; document evidence-driven adjustments and preserve criteria.

Source/API is a researcher workbench, not a multiuser authorization service.
Private projections and provider requests enforce actor information boundaries;
raw researcher frames intentionally contain all state. Treat manual exploration
as intervention and exclude it from estimates. Never label fixture success as a
scientific or live-provider finding.
