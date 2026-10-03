# Phase 1 and 2 acceptance

4 October 2026. T04–T10 are complete for the enabled `enterprise_legacy`
profile, scripted/mock cognition, and passive/monitor defense. This closes the
software foundation milestone; it does not establish hypothesis results,
simulation realism, model performance, or publication readiness.

## Acceptance evidence

| Ticket | Implemented and checked | Evidence |
| --- | --- | --- |
| T04 — service and episode loop | API and CLI use the same live RunManager. Initialize creates a paused world; step advances one joint native tick; start/continue, pause and stop share lifecycle rules. Defender advances once per tick. Events are append-only with a read cursor. Pause/continue preserves scripted outcomes. URL restores replay tick, graph mode, worker view and selection. | `test_run_controls.py`; `test_phase12_acceptance.py::test_cli_api_config_roundtrip_controls_events_and_replay_are_same_run`; browser refresh and temporary-service disconnect/reconnect |
| T05 — visible native behavior | Network/session colors derive from saved native snapshots. Action details retain attempted/concrete action, native TRUE/FALSE/UNKNOWN, local gateway prerequisites and observed changes. Private graph hides unknown names, zones, physical links and peer privileges. Replay reads existing frames only. | Complete-mission browser replay; `test_mission_qualification.py`; `test_engine_bridge.py`; frontend projection tests; outage/action-detail screenshot |
| T06 — configuration workflow | Common numeric bounds use configuration schemas. JSON editor and file import validate through the API; export uses resolved configuration. Resolved settings appear before initialization. Existing run config stays frozen. Invalid targets, duplicate names and impossible topology are rejected. Worker counts change sessions without changing the inherited 16-node world. Interventions are logged and excluded from comparisons. | CLI/API round-trip and ZIP fixture; `test_run_controls.py`; native host-count checks for 1/2/4/8 workers; browser JSON application and zero-action initialization with 3 workers |
| T07 — private knowledge and gateway | Nested prior observations survive later deltas. Own observations and verified peer reports are separate. Known-value gateway binds each worker to its active owned controller and cache. Delivered address/hostname evidence can unlock scanning; it cannot grant ports, sessions or privileges. Forged peer references and coordinator relays created before evidence delivery are rejected. | `test_native_boundaries.py`; `test_engine_bridge.py`; private memory/provenance fixtures in `test_phase12_acceptance.py`; malformed/undelivered decisions in `test_organization_qualification.py` |
| T08 — communication | Star/mesh or a selected directed subset; recipient-copy charges; tick+1+delay delivery; seeded loss; capacity; TTL; inclusive scheduled link interruption. Messages due during interruption become `dropped_link`; later messages can arrive after recovery. No same-tick delivery or adversary recipients. | Transport, reconciliation and seeded-loss fixtures; one-way/recovery/expiry/sparse-topology fixtures; recorded topology in browser replay |
| T09 — organization policies | Hierarchy acts on delivered assignments/reports; swarm acts locally and reconciles delivered claims; independent sends no messages. Branching task fixtures distinguish policy traces. Total loss leaves the hierarchy blind; swarm/independent can act locally. Every architecture obeys the same round-robin team-cap-one schedule. | `test_organization_qualification.py`; parameterized neutral-cap fixture; complete native missions for hierarchy/swarm/independent with 1/2/8 workers |
| T10 — communication inspection | Team graph renders actual configured directed edges and current outages. Worker/coordinator inspectors show claims/assignments and delivered knowledge. Message details retain evidence IDs, due/resolved ticks, bytes and outcomes. Worker/reasoner counts differ for hierarchy. Selection and replay never advance the engine. | Frontend topology/location tests; outage replay and complete-mission browser checks; replay API fixture |

## Verification performed

```powershell
./.venv/Scripts/python.exe -m pytest -q
node --experimental-strip-types --test frontend/tests/research-ui.test.mjs
npm run build --prefix frontend
```

Results: **49 Python tests passed, 4 frontend logic tests passed, production
build passed**. Native checks use Python 3.8.11; service checks use Python
3.13.9; frontend logic checks use Node 24.14.0. The Node test command requires a
runtime with TypeScript stripping; it does not change the app's build runtime
requirements.

Browser checks used a separate temporary data store and service on port 8788:

- Added an interruption with inclusive ticks 2–4 and inspected resolved JSON.
- Applied minimal JSON with defaults, three workers and a specific interrupted
  coordinator link. Initialized and stopped at tick 0: no agent actions, no
  messages, no model tokens. Existing fixture config remained unchanged.
- Replayed a saved two-worker swarm fixture at tick 2. Directed interrupted
  edges matched `dropped_link` deliveries; expanded action details showed
  locally known prerequisites and actor-owned scan-cache changes.
- Refreshed the URL and recovered tick 2, organization mode and Red_0 view.
  Stopped/restarted only the temporary service: disconnection retained the
  frame; polling recovered connectivity without changing replay position.
- Previously replayed a complete hierarchy mission from 0/2 to 2/2 privileged
  targets. The [mission screenshot](../screenshots/complete-mission-software-fixture.png)
  and [interruption screenshot](../screenshots/phase12-link-interruption.png)
  are software evidence, not research results.

All native steps are bounded software fixtures in pytest temporary storage.
No research experiment matrix or live model call was executed. The existing
researcher's live service and paused session were preserved.

## Semantics and next phase

`preconditions` are actor-local gateway checks, not an exhaustive explanation
of each native exploit's internal vulnerability checks. `state_delta` compares
that actor's native view before/after the joint tick, including end-turn effects;
it does not assert that every change was exclusively caused by its requested
action. Private memory retains historical observations; native views show
current sessions and action eligibility. The human researcher can access truth
and all records; private projection is an analytical view, not an API security
boundary.

Reconnect preserves browser context and saved evidence. A service restart marks
unclosed native worlds interrupted; it does not resume simulator checkpoints.
This is intentional and remains documented. Older saved frames without the
new fields remain readable and explicitly say when checks were not recorded.

Proceed to **Phase 3**, starting with T12 qualified linear/branching profiles
and then T13 defense/recovery. T11 live cognition qualification remains separate:
the Ollama adapter exists but has not been exercised against a live model.
Generic topology/access policy, recovery, broader engine qualification, model
validation, batch execution and scientific calibration remain future work.
See [the ordered plan](IMPLEMENTATION_PLAN.md) and [validation limits](VALIDATION_PLAN.md).
