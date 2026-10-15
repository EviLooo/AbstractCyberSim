# Modular settings and temporal evidence checkpoint

Historical 80-test checkpoint. The subsequent [route checkpoint](ROUTE_COMPLEXITY_ACCEPTANCE.md)
adds source-specific caches, scan ages and explicit pivot deployment.

4 October 2026. Implements the next portion of T12a/T12c/T12e over the accepted
CC4 adapter. This does not close Phase 3 or qualify the full complexity table.

## Delivered contract and boundaries

Schema 1.0 remains compatible. An optional CC4-only
`scenario.complexity` contract has module version `1.0` and a `beliefs` module:
`enabled`, `stale_after` (1–1000 ticks), `observation_delay` (0–20 ticks).
Unknown modules, versions and unsupported legacy combinations are rejected
before launching the engine. The proposed schema-2.0 example remains non-executable.

`packages/contracts/module_registry.py` describes supported native population,
observed restoration, temporal evidence and communication mechanisms. Its pure
compiler records effective settings, module versions, seed namespaces, mission,
unsupported extensions and a deterministic manifest hash. Actual physical
inputs remain in the native `world.json`; every frame and run manifest records
the module configuration. The compiler consumes no RNG and excludes architecture.
Changing belief settings does not change the initial physical world fingerprint.

Two development bundles expand to explicit values: native static control and
observed recovery with evidence age. These are not calibrated C0–C3 research
levels. [Executable recovery configuration](../../configs/cc4-recovery.json).
The UI exposes only available mechanisms; parameter bounds come from the public
schema. Editing a preset marks the settings custom. UI, JSON and CLI use the same
validation; edits apply to new environments.

## Observation and decision semantics

The temporal module is opt-in; disabled settings preserve the original private
memory and native behavior. `backend/app/beliefs.py` receives only recipient-local
evidence and own session status, never truth or defender events.

- Tick-zero initial knowledge is immediate. Later host/service observations and
  associated known-target/scan-cache disclosure arrive at the end of their
  observed tick plus configured delay. Decisions on the next tick can use them.
- Own action outcome, busy state and current owned sessions remain immediate.
  This is an explicit simplifying status model, not a delayed-control simulation.
  Immediate action history excludes delayed address/port deltas.
- Queued evidence cannot be forwarded before receipt. Validated address reports
  update only their disclosed fragment; an engine intel response cannot expose
  a recipient's queued local discoveries. Reports do not transfer ports or access.
- Field snapshots preserve source, observation time, receipt time and history.
  Later receipt does not make old evidence fresh. Older out-of-order evidence is
  retained without replacing newer facts. Changed snapshots preserve contradiction
  links; differing sources flag conflicts. Peer reports remain unconfirmed.
- Stale means age reached the threshold, not that the real service is invalid.
  Hidden defender activity does not change evidence age or disclose its cause.
- The enabled scripted policy refreshes aged service scans, including empty
  scans, instead of treating a prior successful action as complete forever.
  Two failed refresh admissions per scan revision/recovery epoch bound retries.
  Own observed session loss starts a new planning epoch. Busy-action waiting is
  unchanged. The coordinator can assign these locally eligible refresh/recovery tasks.
  Age changes the scripted recommendation, not the legal action catalog: both
  hierarchy and swarm can choose to risk an aged actor-owned scan. Fresh scans
  are preferred by scripted assignment/claim ordering, without restricting the
  LLM organizations differently.
- Access loss/recovery events identify individual owned sessions and observed
  hostnames. They do not assert deduplicated team-wide loss or its hidden cause.
  Native eligibility always checks current ownership; delayed evidence cannot
  resurrect a removed or reassigned controller.

The evidence panel shows age, source, observed/received ticks, stale/conflict
status, historical snapshots and observable access events. Private mode selects
only its worker. Researcher mode can inspect all private records alongside the
separate native defender-event panel. Saved frames replay without native steps
or model calls.

## Software evidence

The complete current regression passed **80 tests** (63 prior checks and 17
temporal-module checks), including the action-choice fairness check. Six frontend
tests and the TypeScript/production build passed.

[Temporal fixtures](../../tests/test_temporal_beliefs.py) cover:

| Boundary | Checked evidence |
| --- | --- |
| Contract/compiler | Round trip, architectural independence, invalid versions/modules/ranges, API rejection before worker creation and independent preset copies. |
| Memory | Age versus receipt time, contradictions, unconfirmed reports, out-of-order records, deep-copy isolation and disabled-module equivalence. |
| Delayed privacy | 1/2/4/8 workers; queued discovery and scan evidence stays unavailable; premature target/exploit proposals fail; peers do not acquire it automatically; intel views cannot leak queued local knowledge. |
| Refresh/organization | Aged scans become eligible, stale exploits yield to verification, owned loss re-enables planning and hierarchy can assign a refresh previously completed. |
| Physical reset/pairing | Baseline, disabled settings and enabled swarm materialize the same initial world without actions; new channel/event state is empty. |
| Static integration | Two-worker hierarchy/swarm/independent missions finish under delay 2, age 20 and controlled zero-addon services, without interventions/providers. |
| Native recovery | Native Monitor/Restore removes acquired restricted-zone sessions. Legal re-scan/exploit restores access; private state gives symptoms without a Restore/Blue cause. |
| Artifacts/UI | A real Run saves loss, recovery and historical evidence; replay retains it. Frontend projection excludes peer records and truth from private evidence. |

Browser checks cover preset expansion/custom edits, paused three-worker
initialization, private evidence rendering and copied software-fixture replay.
The updated preview is **http://127.0.0.1:8790** with separate
`.local/temporal-workbench` storage. Older sessions on 8787/8788/8789 are preserved.
The live preview remains at tick zero. A copied stopped/manual software fixture,
clearly named as a software check, provides a restoration/recovery replay;
it is excluded from evaluation and is not a paper result.

[Initialized private view](../screenshots/temporal-initialized-workbench.png).
[Saved recovery evidence](../screenshots/temporal-recovery-replay.png).

## Still pending

The full generic compiler, alternative technical routes/dependencies, arbitrary
topology, isolation/patching, configurable discovery scope/sensor coverage,
qualified service-change transitions, mission dwell/deadlines and C0–C3
calibration remain pending. No scientific metric for recovery is claimed here;
the observable event history is available for the later versioned reducers.

All knobs have validated ranges, but not every combination has a solvable
mission or a qualified difficulty interpretation. Delay greater than the age
threshold can make delivered evidence already stale. This is explicit,
not silently corrected. Native high-level exploit selection stays internal.
Large evidence histories may hit the provider's explicit context limit;
evidence-preserving summarization and live-model qualification remain pending.

Only bounded software fixtures ran. No live LLM calls, research experiment
matrix, training, architecture ranking or realism/superiority claim was produced.
Next: T12b/T12d, qualifying route/dependency structure and sustained multi-target
access/recovery conditions before research baselines and live evaluation.
