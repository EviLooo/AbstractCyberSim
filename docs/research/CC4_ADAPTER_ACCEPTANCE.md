# CC4 adapter implementation and acceptance

4 October 2026. The CC4 adapter is implemented alongside the legacy backend and
selectable in the workbench. This completes the initial adapter integration
milestone, not Phase 3 or the scientific environment/evaluation program.

Follow-up: [modular settings and temporal evidence](TEMPORAL_COMPLEXITY_ACCEPTANCE.md)
implements the next portions of T12a/T12c/T12e. Counts and pending items below
describe this earlier adapter gate; the follow-up records current status.

## Delivered

- A separately pinned, unmodified CC4 checkout and isolated Python 3.12 worker.
  Startup checks revision, source cleanliness, interpreter, Gym and NumPy pins.
  Neither simulator is imported by the service.
- A research generator over native enterprise zones/templates. Logical
  `Red_0`–`Red_7` map to native CC4 names. Workers own separate sessions and scan
  caches, share a declared contractor foothold, and retain cross-zone ownership.
  This deliberately changes CC4's territorial attacker model.
- Profile validation, registry, presets and an executable [CC4 config](../../configs/cc4.json).
  UI/CLI settings expose workers, per-zone user/server populations, maximum
  addon services, targets, and restore response delay/cooldown/budget. Targets
  exist at minimum population; incompatible legacy settings are rejected.
- Known-only native views and provenance-checked delivered intelligence. CC4
  observation names are normalized at the boundary. Reports cannot grant
  sessions, privileges or peer port caches.
- Native multi-tick admission, waiting and completion. Busy workers make no
  further cognition calls. Team-cap-one permits one in-flight team action.
  Continuation records do not inflate attempts, duplicates or retry counts.
- Passive, Monitor-only and bounded observe-and-restore defense. The active
  policy reads **fresh native Monitor results**, not startup process inventory
  or true compromise state. Signal/decision/effect times are logged. Unnecessary
  restores remain possible; this is a simple control policy.
- Independent offensive scoring, deduplicated targets, total-access-loss
  termination, manifests, native snapshots and offline replay/export.
- Profile controls, busy-action status/duration, readable native-zone graph
  labels and a researcher-only panel separating intended policy from firewall blocks.

The adapter is split into `cc4/scenario.py`, `cc4/defender.py` and `cc4/runtime.py`.
Serialization is shared in `engine_worker/common.py`. The bridge selects a
separate interpreter from the profile; organizations, transport, providers,
storage and visualization stay shared. Legacy remains the default configuration.

## Validation evidence

The full Python regression passed **61 tests**. Two subsequently added CC4
API/population checks passed separately: **63 passing checks across the current
suite** (49 existing, 14 CC4). Five frontend checks and the TypeScript/production
build pass. No model calls, training or research matrix ran.

[CC4 tests](../../tests/test_cc4_adapter.py) establish:

| Fixture | Evidence |
| --- | --- |
| 1/2/4/8 workers | Joint discovery, private scan cache, unscanned-exploit rejection, independent newly acquired sessions, deduplicated host count. |
| Durations | Stock exploitation has three IN_PROGRESS frames and one completion; no resubmission or extra ticks per worker. |
| Reset/pairing | Repeated create materializes identical worlds; changing architecture preserves the initial world fingerprint. |
| Verified delivery | Sender discovery does not update peers automatically. Forged evidence is rejected; delivery unlocks scanning without ports/sessions. |
| Complete missions | Hierarchy, swarm and independent scripted teams reach privileged restricted-zone access, close their workers and retain offline frames. Zero-addon service fixtures isolate integration behavior. |
| Reactive recovery | Fresh Monitor signals trigger delayed native Restore. Acquired target access disappears, a loss delta is saved and native completion is logged. |
| Response limits | Delay, cooldown, budget and known-host admission are checked without a truth inventory. |
| Busy/capacity | Waiting workers make no extra cognition calls; one-team capacity cannot admit another action while busy. Metrics count admissions. |
| API/artifacts | Profile round trip, paused initialization, busy manual rejection without advancing, stop/cleanup and a readable evidence ZIP. |
| Population | Minimum-to-maximum settings materialize 96 additional hosts without actions. This does not qualify missions at every size. |

Browser verification covers profile/default-target switching, response/population
controls, three-worker initialization at tick zero, native graph rendering and
the phase/policy panel. A copied completed pytest fixture supports UI replay
inspection without executing another episode. The live browser fixture has taken
no actions. [Workbench screenshot](../screenshots/cc4-initialized-workbench.png).
The saved replay shows `IN_PROGRESS` at tick 33 (one native tick remaining),
completion and privileged mission success at tick 34, with execution controls
disabled. No replay action is executed again.

The original service/session on 8787 was preserved. The updated preview uses
**http://127.0.0.1:8788** and separate `.local/cc4-workbench` data.

## Setup

This laptop is ready. On another Windows installation, install service/frontend
dependencies first, then:

```powershell
./tools/setup_cc4.ps1 -Python 'C:\Program Files\Python312\python.exe'
./tools/start.ps1
```

The script preserves existing work and installs simulator-only pins in
`engine/cc4.requirements.lock`, without the upstream Ray/Torch training stack.
`.env.example` documents optional interpreter/checkout overrides. Select
**Enterprise · CAGE Challenge 4** before initializing.

## Remaining scope

- The full T12 complexity registry/compiler, richer topology/dependencies,
  timestamped stale/delayed beliefs, multi-target dwell/re-entry and service
  patching are pending. Arbitrary graphs need separate implementation and tests.
- Green activity, phishing, free respawn and exposed decoy/Impact actions are
  disabled or outside this catalog. Their multi-worker interactions need qualification.
- Restore is the enabled active response. Native block/allow were audited but
  are not yet part of the reactive policy.
- Complete-mission checks use controlled services. Mixed-service worlds may
  legitimately fail; success or LLM superiority is never guaranteed.
- High-level exploitation still chooses a technique internally. Explicit
  technique-choice reasoning needs a qualified action extension.
- Live LLM qualification, strong adaptive baselines, behavioral calibration,
  frozen research scenarios and scientific experiments remain pending.
- Full upstream CC4 pytest/wrapper compatibility is unverified: its conftest
  requires the omitted Ray stack.

Next: T12a/T12c, beginning with explicit module capabilities and timestamped
private beliefs/observable recovery over this adapter, before live experiments.
