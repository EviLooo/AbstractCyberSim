# AbstractCyberSim

Local workbench for studying how offensive cyber agent organizations behave in CybORG. The application provides network and team visualization, private-agent inspection, tick controls, message transport, saved replay, configuration, and an experiment planner.

The full approved graduation software scope is implemented and qualified through
R7. The42-item final audit is saved in docs/research/FINAL_ACCEPTANCE_AUDIT.md. The
[approved scope](docs/research/APPROVED_SCOPE.md),
[persistent execution Goal](docs/research/GRADUATION_EXECUTION_GOAL.md),
[requirement ledger](docs/research/GRADUATION_REQUIREMENTS.md) and
[checkpoint](docs/research/GRADUATION_CHECKPOINT.md) define the work and evidence.
The earlier four-worker hierarchy failure has been fixed and verified without
raising its budgets. Historical acceptance figures below refer to older profiles.
Scientific results, expert realism review and successful live-model qualification
remain outstanding. No real targets are scanned or attacked.

Use the current [researcher guide](docs/research/RESEARCHER_GUIDE.md),
[programmer handoff](docs/research/PROGRAMMER_HANDOFF.md) and
[simple presentation](docs/research/GRADUATION_PRESENTATION.md).
The local graduation demo is **http://127.0.0.1:8797**. Select
**Graduation · investigative CC4**; recipes and conditions, 1/2/4 workers,
hierarchy/swarm/independent, evidence/transport delay, shared Patch or Restore,
budgets and target hold/deadline are configurable. Initialize paused, then use
explicit Step/Run controls. Replay/export make no model calls. Scripted controllers
can succeed; the research does not assume a guaranteed LLM winner.

Fresh research-only setup:

```powershell
./tools/setup_research.ps1 -ServicePython python -CC4Python 'C:/path/to/python312.exe'
.venv/Scripts/python.exe -m backend.app.cli serve --port 8787
```

Implementation branch: `research-workbench`, based on the existing repository's `main`. The older Mesa prototype remains on `v-0.2`. Keep both in this repository; merge the workbench branch when it is reviewed. CybORG is a separate pinned Git submodule plus a documented two-line source patch.

## Start on this laptop

From the repository directory in PowerShell:

```powershell
./tools/start.ps1
```

Open **http://127.0.0.1:8787**. The service environment is `.venv` (Python 3.13.9).
Legacy uses `cyborg38` (Python 3.8.11); the selectable CC4 engine uses
`.engine/cc4/venv` (Python 3.12.5). Opening the server/page starts no actions or model calls.

The latest observed-search preview runs at **http://127.0.0.1:8796**, with separate
data in `.local/search-preview`, preserving earlier preview services. Select
**Enterprise · CAGE Challenge 4** in Laboratory. [Adapter acceptance and limits](docs/research/CC4_ADAPTER_ACCEPTANCE.md).

In Laboratory, select hierarchy/swarm/independent, choose 1–8 cyber workers, configure seeds and transport, then **Initialize environment**. This creates a paused native CybORG world. **Step** executes one joint tick; **Run**, **Pause**, and **Stop** control subsequent ticks. Click hosts or team members, switch researcher/private views, and use the replay slider to inspect saved evidence.

For the search baseline, import `configs/cc4-search-tradeoffs.json` or choose
**Scripted → Local search · observed routes and deadline**. Search settings
control risk/failure/unknown-connection penalties and expansion limits; saved
decision panels show estimated plans. [Semantics and qualification](docs/research/OBSERVED_SEARCH_ACCEPTANCE.md).

Configuration changes apply to new runs. In exploration mode, manual actions are logged and make a run ineligible for evaluation comparisons. Evaluation runs prohibit manual actions. Restarting the service preserves replay evidence, but does not resume a native simulator checkpoint.

For different route choices, import `configs/cc4-tradeoffs.json` or choose
**Environment complexity → Fast exposed / slower quiet routes**. Configure
SSH/FTP action times, sensor exposure, optional root-service gateways and
temporary service blocking. Add a mission deadline to create time pressure.
Increase user hosts per zone before adding alternatives (up to nine).
[Exact mechanisms and software evidence](docs/research/ROUTE_TRADEOFFS_ACCEPTANCE.md).
[Explicit implemented/open requirements](docs/research/COMPLETION_LEDGER.md).

CC4 actions span native ticks; busy workers wait without extra cognition calls.
The optional temporal module adds host/service observation delay, evidence age,
source/history/conflicts and observable access loss/recovery. Use **Evidence age
and recovery** to configure it, or import `configs/cc4-recovery.json`. Own action
results and session status remain immediate. [Semantics and acceptance](docs/research/TEMPORAL_COMPLEXITY_ACCEPTANCE.md).
Settings expose host/service counts and optional bounded sensor-driven recovery.
The environment panel separates intended policy from actual firewall blocks.
Green activity, phishing and automatic respawn are disabled in this profile.

Install the CC4 backend with an isolated Python 3.12 interpreter:

```powershell
./tools/setup_cc4.ps1 -Python 'C:\Program Files\Python312\python.exe'
```

This pins an unmodified checkout and simulator dependencies without the upstream
RL training stack. Keep both CybORG distributions in separate environments.

## Installation on another Windows laptop

Requires Git, Node.js 20.19+ / 22.12+, Python 3.12+ for the service, and Python 3.8 for the pinned legacy simulator. The verified Node version here is 24.14.0. Conda is one way to provide the engine interpreter:

```powershell
git clone --recurse-submodules --branch research-workbench https://github.com/EviLooo/AbstractCyberSim.git
cd AbstractCyberSim
conda create -n cyborg38 python=3.8.11 -y
./tools/setup.ps1 -EnginePython "$env:USERPROFILE/anaconda3/envs/cyborg38/python.exe"
./tools/start.ps1
```

The implementation branch must be pushed before another person can clone it. The commands above describe the installation workflow, not a claim that this local branch is already published.

If using another engine interpreter location, set it before startup:

```powershell
$env:CYBORG_PYTHON = 'C:/path/to/python38/python.exe'
./tools/start.ps1
```

`setup.ps1` preserves the existing dependency checkout, installs locked dependencies, verifies the pinned revision, applies the reviewed source patch, and builds the frontend. It does not run tests or research episodes. The service and engine must use different Python environments. Locks capture this Windows installation; other operating systems need their own qualification. `.env.example` documents optional environment variables; `.env` files are not loaded automatically.

## Cognition and organization

- **Scripted** is a deterministic software baseline, explicitly labeled as having no LLM. No API key or cloud infrastructure is required.
- **Hierarchy** has N native workers and an additional cognitive coordinator. Workers report through a star topology, receive assignments on later ticks, and act only on eligible delivered assignments. The coordinator has no native sessions or hidden world inventory.
- **Swarm** workers exchange local claims over a mesh and break observed conflicts locally. They have no global allocator or shared private memory.
- **Independent** disables team messages and uses each worker's local knowledge.
- **Ollama** is an implemented optional local provider adapter. Start Ollama and install a model yourself, then select its exact model tag. The adapter uses structured JSON, per-call timeouts, transcript logs, conservative budget reservations, actual reported usage, and one bounded worker format repair. Live model calls were not made or validated during this implementation. Hosted provider adapters are future work.

Communication is a separately modeled research overlay with delay, loss, TTL, per-tick capacity, selected directed links and scheduled link interruptions. It is not native cyber-network congestion. Delivered engine-verified address/hostname evidence can make a recipient's scan eligible; it never grants another actor's ports cache, privileges, or sessions. Worker inspectors distinguish self-observed facts from verified peer reports.

## Repository layers

```text
CybORG/                    pinned upstream submodule; existing local files preserved
engine/                    manifest, dependency lock, compatibility-patch notes
packages/contracts/        strict Pydantic models + generated JSON schemas
packages/engine_worker/     isolated legacy/CC4 adapters, action gateways, JSONL worker
backend/app/               modern API, process bridge, cognition, organizations,
                           communication, run lifecycle, storage, evaluation
frontend/                  React/TypeScript + Cytoscape interface; npm lock
configs/                   executable schema-1.0 episode and experiment configs
prompts/                   versioned worker/coordinator prompt sources
tests/                     software contract, transport, lifecycle, engine checks
tools/                     installation/startup/patch/schema scripts
docs/research/             research design and protocol, historical audit
artifacts/                 local SQLite index and evidence (ignored by Git)
```

Only `packages/engine_worker` imports CybORG. UI and CLI configuration share backend contracts. Change algorithms in `policies.py`, cognition adapters in `providers.py`, native actions/scenarios in the engine adapter, and metrics in `evaluation.py`. Regenerate contracts after editing configuration models:

```powershell
./.venv/Scripts/python.exe tools/generate_contracts.py
npm run contracts --prefix frontend
npm run build --prefix frontend
```

The schema script also refreshes default files in `configs/`; keep custom configurations under different filenames.

## Configuration, planning, and exports

The UI edits common settings and provides a JSON editor for all settings. Resolved, validated settings appear before initialization. Import/export uses the same `EpisodeConfig` consumed by the CLI. The experiment planner expands organization × workers × world seeds × transport × replicates, validates each job, and exports a resolved matrix. It **does not execute batches** in this release.

```powershell
./.venv/Scripts/python.exe -m backend.app.cli validate configs/hierarchy.json
./.venv/Scripts/python.exe -m backend.app.cli preview configs/comparison.json
./.venv/Scripts/python.exe -m backend.app.cli list
```

Each saved run contains immutable config, materialized initial world, engine/source/prompt fingerprints, JSON state frames, append-only events, native stderr, metrics, and provider transcripts when used. The UI exports a ZIP evidence bundle and metrics CSV. Replay reads frames and does not call the engine or cognition provider.

With the local service running, the CLI can use that same live environment:

```powershell
./.venv/Scripts/python.exe -m backend.app.cli initialize configs/hierarchy.json
# Substitute the returned run ID below. Step/start execute agent actions.
./.venv/Scripts/python.exe -m backend.app.cli step RUN_ID
./.venv/Scripts/python.exe -m backend.app.cli control RUN_ID start
./.venv/Scripts/python.exe -m backend.app.cli control RUN_ID pause
./.venv/Scripts/python.exe -m backend.app.cli control RUN_ID continue
./.venv/Scripts/python.exe -m backend.app.cli control RUN_ID stop
./.venv/Scripts/python.exe -m backend.app.cli frame RUN_ID --tick 0
./.venv/Scripts/python.exe -m backend.app.cli events RUN_ID --after 0
```

These commands accept `--port` (default 8787). `initialize` requires the running
service and creates a paused world; it no longer creates and immediately closes
an offline native process. `frame` and `events` read evidence without actions.

In **Links, interruptions & capacity**, `links: null` keeps the declared star or
mesh; a directed list selects its subset, and `[]` disables every link.
Interruption `start_tick`/`end_tick` are inclusive; nullable sender/recipient
match any endpoint, and `bidirectional` also matches the reverse direction.
Messages due during an interruption are permanently `dropped_link`; they are
not retried. TTL expiry takes precedence. Later messages can arrive after
recovery. Configuration changes always apply to a new environment.

The page URL preserves the selected run, replay tick, graph mode, private view
and inspector selection. Refresh or service reconnection restores that context.
Action details show actor-local gateway checks and observed changes over the
joint tick, including end-turn effects.

Comparison excludes manual, unfinished, non-evaluation, and unknown-usage runs. It matches actual world and numerical conditions, keeps failures/censoring, and provides a descriptive paired success estimate with world-cluster bootstrap intervals when at least two paired worlds exist. See [implementation status](docs/IMPLEMENTATION_STATUS.md) for limitations before interpreting this as final paper analysis.

## Software verification

Choose **Decision policy** under Scripted for local rules or local replanning.
Retry/backoff settings, remembered local facts, considered choices and cost
estimates are saved; the decision panel has a readable choice table and private
worker projection. Use [`configs/cc4-local-replan.json`](configs/cc4-local-replan.json)
or [`configs/cc4-local-rules.json`](configs/cc4-local-rules.json).
[Acceptance and limits](docs/research/BASELINE_DIAGNOSTICS_ACCEPTANCE.md).

CC4 also supports configurable sustained access, inclusive deadlines and live
privileged-host prerequisites. Use [`configs/cc4-mission.json`](configs/cc4-mission.json)
or **Mission duration and objectives**. Researcher replay displays confirmed
holds, resets and failures; private views show only owned access and public
requirements. [Semantics and acceptance](docs/research/MISSION_COMPLEXITY_ACCEPTANCE.md).

CC4 now includes opt-in segmented source routes. Use
[`configs/cc4-routes.json`](configs/cc4-routes.json), or select **Segmented routes
and alternatives** under **Environment complexity**. Configure 1–3 gateway
layers, 1–2 alternatives and optional hardened SSH dead ends. The route flow
shows actual source permissions separately from the physical network. Manual
actions can select an owned source; `EstablishPivot` is an explicit privileged
deployment extension with an empty scan cache. Native firewall checks and
restoration still decide execution. [Semantics and limits](docs/research/ROUTE_COMPLEXITY_ACCEPTANCE.md).

```powershell
./.venv/Scripts/python.exe -m pytest -q
node --experimental-strip-types --test frontend/tests/research-ui.test.mjs
npm run build --prefix frontend
```

Engine checks take bounded fixture steps in temporary test storage; these are software checks, not research experiments or LLM studies. The complete current regression passed 116 Python tests. Coverage includes native missions, actor ownership, delivered-only coordination, scheduling, API/CLI parity, CC4 action durations, observed restoration, delayed evidence privacy and temporal recovery. Nine frontend checks cover replay context, private projection, topology, CC4 labels, private belief evidence, private route projection and private mission projection and private decision projection; the production build passes on Node 24.14.0. See the [CC4 adapter acceptance](docs/research/CC4_ADAPTER_ACCEPTANCE.md), [Phase 1–2 acceptance checklist](docs/research/PHASE_1_2_ACCEPTANCE.md), exact fixtures and limits in the [validation plan](docs/research/VALIDATION_PLAN.md), and the [native action explanation](docs/NATIVE_ACTION_LOGIC.md).

## Research status

This is an implemented workbench with software acceptance, not completed research. Both the legacy Scenario2 enterprise and isolated CAGE Challenge 4 enterprise profiles are selectable. CC4 adds configurable native zone populations, multi-tick actions, bounded observed restoration and opt-in temporal evidence modules and segmented source routes. Richer modular complexity, arbitrary topology, service-disruption objectives, batch execution/resumption, model generalization and scientific calibration remain pending. The full proposed research is in [docs/research/README.md](docs/research/README.md).

Framework documentation: [CybORG](https://github.com/cage-challenge/CybORG), [FastAPI](https://fastapi.tiangolo.com/), [React](https://react.dev/learn), [Cytoscape.js](https://js.cytoscape.org/), [Ollama chat API](https://docs.ollama.com/api/chat). Upstream CybORG retains its license in the submodule.
