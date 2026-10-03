# AbstractCyberSim

Local workbench for studying how offensive cyber agent organizations behave in CybORG. The application provides network and team visualization, private-agent inspection, tick controls, message transport, saved replay, configuration, and an experiment planner.

Implementation branch: `research-workbench`, based on the existing repository's `main`. The older Mesa prototype remains on `v-0.2`. Keep both in this repository; merge the workbench branch when it is reviewed. CybORG is a separate pinned Git submodule plus a documented two-line source patch.

## Start on this laptop

From the repository directory in PowerShell:

```powershell
./tools/start.ps1
```

Open **http://127.0.0.1:8787**. The installed service environment is `.venv` (Python 3.13.9). The engine uses the existing `cyborg38` environment (Python 3.8.11). No simulation, experiment, or model call starts when the server or page opens.

In Laboratory, select hierarchy/swarm/independent, choose 1–8 cyber workers, configure seeds and transport, then **Initialize environment**. This creates a paused native CybORG world. **Step** executes one joint tick; **Run**, **Pause**, and **Stop** control subsequent ticks. Click hosts or team members, switch researcher/private views, and use the replay slider to inspect saved evidence.

Configuration changes apply to new runs. In exploration mode, manual actions are logged and make a run ineligible for evaluation comparisons. Evaluation runs prohibit manual actions. Restarting the service preserves replay evidence, but does not resume a native simulator checkpoint.

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

Communication is a separately modeled research overlay with delay, loss, TTL, and per-tick capacity. It is not native cyber-network congestion. Delivered engine-verified address/hostname evidence can make a recipient's scan eligible; it never grants another actor's ports cache, privileges, or sessions.

## Repository layers

```text
CybORG/                    pinned upstream submodule; existing local files preserved
engine/                    manifest, dependency lock, compatibility-patch notes
packages/contracts/        strict Pydantic models + generated JSON schemas
packages/engine_worker/     Python 3.8 native scenario, action gateway, JSONL worker
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

The UI edits common settings and provides a JSON editor for all settings. Import/export uses the same `EpisodeConfig` consumed by the CLI. The experiment planner expands organization × workers × world seeds × transport × replicates, validates each job, and exports a resolved matrix. It **does not execute batches** in this release.

```powershell
./.venv/Scripts/python.exe -m backend.app.cli validate configs/hierarchy.json
./.venv/Scripts/python.exe -m backend.app.cli preview configs/comparison.json
./.venv/Scripts/python.exe -m backend.app.cli list
```

Each saved run contains immutable config, materialized initial world, engine/source/prompt fingerprints, JSON state frames, append-only events, native stderr, metrics, and provider transcripts when used. The UI exports a ZIP evidence bundle and metrics CSV. Replay reads frames and does not call the engine or cognition provider.

Comparison excludes manual, unfinished, non-evaluation, and unknown-usage runs. It matches actual world and numerical conditions, keeps failures/censoring, and provides a descriptive paired success estimate with world-cluster bootstrap intervals when at least two paired worlds exist. See [implementation status](docs/IMPLEMENTATION_STATUS.md) for limitations before interpreting this as final paper analysis.

## Software verification

```powershell
./.venv/Scripts/python.exe -m pytest -q
npm run build --prefix frontend
```

Engine checks take bounded fixture steps in temporary test storage; these are software checks, not research experiments or LLM studies. They verify 1/2/4/8 actor discovery, scans, exploit/session ownership, action rejection, verified-address sharing, hierarchy delivery semantics, saved replay, and matched world identities.

## Research status

This is the first implementation of the workbench, not completed research. The enabled native profile is CybORG's legacy Scenario2 enterprise (13 hosts plus three routers), with passive/monitor-only defense and a privileged-access mission. Four-zone custom layouts, recovery defense, disruption objectives, batch execution/resumption, model generalization, and final study calibration remain pending. The full proposed research is in [docs/research/README.md](docs/research/README.md).

Framework documentation: [CybORG](https://github.com/cage-challenge/CybORG), [FastAPI](https://fastapi.tiangolo.com/), [React](https://react.dev/learn), [Cytoscape.js](https://js.cytoscape.org/), [Ollama chat API](https://docs.ollama.com/api/chat). Upstream CybORG retains its license in the submodule.
