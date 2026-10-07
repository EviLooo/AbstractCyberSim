# Workbench implementation status

**6 October 2026:** all required graduation software gates R0–R7 are accepted.
Immutable splits/source/model binding, paired analysis/plots/reproduction,
final UI/demo and every-item audit are verified; see
[final acceptance](research/FINAL_ACCEPTANCE_AUDIT.md). The required
investigation, credentials, capabilities, Patch/Restore and organization behavior
are implemented and native-tested. Current status is in
[GRADUATION_REQUIREMENTS](research/GRADUATION_REQUIREMENTS.md) and
[GRADUATION_CHECKPOINT](research/GRADUATION_CHECKPOINT.md). Historical status below
remains evidence for older profiles, not a current incomplete-feature list.
Scientific/expert review and live-provider qualification remain outstanding.

4 October 2026 — Phase 1–2 software acceptance completed for the enabled legacy/scripted profile, local branch `research-workbench`. [Per-ticket evidence](research/PHASE_1_2_ACCEPTANCE.md).

## Implemented

**Observed search and wider route qualification (5 October):** separate
`local_search` policy with time/risk/deadline estimates, bounded observed-graph
search, persistent connection facts shared by all providers, configurable
weights and saved/UI plans. Fixed 1–8-worker, 1–3-layer, 2/3/9-alternative,
0/3/5-addon witnesses and native restoration during service quarantine pass.
149 Python tests, eleven frontend checks and the production build pass.
[Exact acceptance and research boundaries](research/OBSERVED_SEARCH_ACCEPTANCE.md).
Phase 3 remains incomplete; calibration, live LLM controls and remaining core
mechanisms stay explicitly open in the ledger.

**Generated route tradeoffs (T12b extension, 5 October):** seeded native SSH/FTP
gateways, user/root service outcomes, configurable native exploit durations,
partial scan assessments and a separate traffic sensor that temporarily changes
native service ACLs. Controls and researcher/private visualization are delivered.
[Exact effects, checks and limits](research/ROUTE_TRADEOFFS_ACCEPTANCE.md).
Whole tickets remain open where qualification is incomplete; use the
[completion ledger](research/COMPLETION_LEDGER.md) before changing milestone order.

**Local baseline and diagnostics checkpoint (bounded T12f):** versioned local
rules and observed-frontier replanning, shared remembered facts for all providers,
configurable retries/backoff, source-aware delivered coordination, saved choices,
readable UI cost tables and offline/CSV diagnostics are delivered. Both policies
complete bounded C0/C1/C2 development fixtures; hierarchy/swarm checks retain
distinct assignment/claim traces. **116 Python tests**, **nine frontend checks**
and the build pass. No research experiments or live LLM calls were made.
[Semantics, fixtures and limits](research/BASELINE_DIAGNOSTICS_ACCEPTANCE.md).
Still open: **T11 live-model qualification and broader scenario calibration**.
The later route-tradeoff extension above fills a missing environment requirement;
review the ledger before advancing past other open core requirements.
This is not closure of Phase 3 or a calibrated scientific complexity ladder.

**Sustained missions (bounded T12d primitives):** configurable simultaneous
privileged-access holds, inclusive mission/objective deadlines and live
privileged-host prerequisites. Native defender effects reset affected progress;
legal recovery is checked. UI controls, truth/private views, replay and metric
exports are delivered. **101 Python tests**, **eight frontend checks** and the
build pass. No research experiments or model calls were made.
[Semantics and acceptance](research/MISSION_COMPLEXITY_ACCEPTANCE.md).
Followed by the bounded baseline/diagnostics checkpoint above.

**Segmented routes (first bounded T12b profile):** adjustable 1–3 gateway
layers, one/two alternative sources and hardened SSH dead ends. Actual native
host blocks gate scanning/exploitation; explicit `EstablishPivot` deployment
requires actor-owned privileged access. Private source selection, independent
caches, restoration/recovery and route visualization are delivered. The complete
regression passes **92 Python tests**, plus **seven frontend checks** and the
build. No experiments or model calls were made.
[Semantics, evidence and limits](research/ROUTE_COMPLEXITY_ACCEPTANCE.md).
Followed by the sustained mission checkpoint above.

**Modular settings and temporal evidence:** opt-in CC4 observation delay/age,
source-preserving private history/conflicts, legal refresh/replanning after
observable loss, capability-derived controls and offline recovery evidence.
The complete 80-test regression passed; six frontend checks
and the build pass. This is partial T12a/T12c/T12e, not all of Phase 3.
[Detailed semantics and limits](research/TEMPORAL_COMPLEXITY_ACCEPTANCE.md).

**CC4 adapter implemented alongside legacy:** selectable isolated workers,
native durations, controlled populations and bounded sensor-driven restore
defense are delivered. The full 61-test regression passed, plus two added
API/population checks; five frontend checks and the build pass. Phase 3 and
research calibration remain incomplete. Full upstream Ray/wrapper compatibility
is not claimed. [Evidence and limits](research/CC4_ADAPTER_ACCEPTANCE.md).

| Area | Delivered behavior |
| --- | --- |
| Repository | Existing AbstractCyberSim remote; implementation branch from main; pinned CybORG submodule; two-line actor-owned Portscan lookup patch; separate runtime locks. |
| Contracts | Strict schema-1.0 configuration/action/experiment models; checked-in JSON Schemas; generated TypeScript config types; API/CLI validation. Design examples remain separate. |
| Native adapter | Fresh enterprise Scenario2 generation per run, 1–8 independently owned worker sessions, external Sleep defaults, passive/monitor presets, discovery/scan/exploit/escalation catalog, invalid-action rejection. |
| Privacy | Known=True native parameters only; own sessions/cache; separate truth channel; private observations/history/inboxes; engine-proven address/hostname intel; no port/session grants. |
| Organizations | Hierarchy star report/assignment pipeline and bootstrap waiting; swarm local claims/tie-breaking; independent baseline; per-worker and neutral team-cap-one scheduling. |
| Communication | Recipient-copy envelopes, tick+1+delay delivery, seeded loss, bytes/envelope caps, TTL, directed sparse links, inclusive scheduled interruptions and delivery status logs. Explicit overlay. |
| Cognition | Deterministic scripted baseline; optional Ollama structured provider, serial conservative reservations, actual/unknown usage accounting, worker format repair, saved transcripts. No live provider call made. |
| Controls/storage | Initialize paused; shared API/CLI live loop; single joint tick; run/pause/continue at tick boundaries; stop; four-live-world cap; SQLite index; config/world/manifest/events/frames; restart marks native state interrupted; offline replay and event cursors. |
| UI | Configuration editor/import/export/JSON and resolved settings; actual network and directed organization graphs with outages; selected-worker view; self-observed/peer-reported knowledge; host/worker/coordinator inspector; attempted/native/concrete actions, local checks, state changes and TRUE/FALSE/UNKNOWN; message timeline; URL-restored replay; automatic reconnect; manual actions flagged. |
| Planning/evaluation | Matrix validation/preview/export; deduplicated controlled/privileged hosts and targets; attempts/invalid/duplicate/message/usage reducers; ZIP and CSV exports; descriptive paired success comparison with exclusions and world clustering. |

## Checked

`pytest -q`: **49 passed**. Checks execute bounded technical fixtures in pytest temporary directories and never call a live model. They are not hypothesis experiments. Complete native missions reach both Enterprise2 and Op_Server0 with hierarchy/swarm/independent teams of 1, 2 and 8 workers, requiring active privileged target access. Native discover/scan/exploit paths also cover 4 workers. Blocked routes, actor ownership, inactive sessions, verified intel, delivered-only task/claim behavior, total message loss, the joint native schedule and pause/continue determinism are checked. New fixtures cover directed interruption/recovery, provenance forgery and undelivered relays, persistent nested facts, shared CLI/API configuration/lifecycle, neutral team capacity, and sparse hierarchy waiting. Existing mocked-provider checks cover charged repairs and unknown usage. Exact settings, assertions and limits are in [the validation plan](research/VALIDATION_PLAN.md).

The qualification fixes privileged-host inspection (needed even when an exploit grants root/SYSTEM), actor-scoped coordinator completion, recipient controller binding and inactive-foothold escalation. Saved frames expose the native step counter without fabricating execution of filtered Sleep actions.

`npm run build --prefix frontend` passed: generated contracts type-check and the production application builds. **4 frontend logic tests pass** for private projection, topology and replay location. In-app browser verification covers resolved outage settings, JSON defaults, three-worker initialization at tick 0, archived outage replay/action details, refresh and temporary-service reconnect, in addition to earlier planner/complete-mission checks. Fresh installations start with an empty data store.

Complete-mission replay is also visually checked: 0/2 targets at initialization, 2/2 at completion, native exploit outcome, privileged target nodes and hierarchy topology. [Screenshot](screenshots/complete-mission-software-fixture.png) records the archived pytest fixture. Existing researcher sessions were preserved; these checks use a separate temporary replay service.

The upstream CybORG acceptance API module previously passed: 7 passed, 1 skipped. Targeted native discovery/scan/escalation success and host-count checks now pass: **55 passed, 24 skipped, 526 deselected**. Exploit success/host-count cases in this selection are skipped upstream; they are not claimed verified by that command. Workbench exploit and mission fixtures supply the checked exploit coverage. Existing Python/Gym deprecation warnings remain.

## Pending from the full research design

Phase 3 has been redesigned around independently configurable behavioral
complexity modules; see [the updated environment handoff](research/ENVIRONMENT_COMPLEXITY_DESIGN.md)
and [T12a–T12f/T13](research/IMPLEMENTATION_PLAN.md). Hierarchy versus swarm stays
the main comparison. The bounded CC4 contract/compiler, observed restoration, timestamped beliefs,
segmented routes and sustained mission primitives are implemented as documented
above. Wider profile qualification and scientific calibration remain pending.

- Generic four-zone generator, network variation beyond the inherited scenario, qualified linear/branching/recovery families, and explicit generic zone-access policy.
- Qualified active defender and service-disruption mission. Monitor observes; it does not remediate.
- The full upstream regression suite and every exploit/escalation precondition, generic NACL/block/bandwidth semantics, inactive-session behavior in the inherited operational gate, and broad seed solvability/difficulty calibration. Fixed legacy scan/exploit disconnection and actor-local operational-gate boundaries are checked.
- Live Ollama/model verification, hosted providers, coordinator schema repair, evidence-preserving context summarization, pinned model digests, and provider seed/generalization studies.
- Batch job execution/resumption/retry manager and experiment-launch controls. The planner exports jobs only. No research experiments are run or scheduled.
- Final pairing by explicit replicate IDs, prespecified treatment interactions, missing/refused/technical-error outcome handling for final analysis, budget frontiers, and publication-quality plots.
- Full CC4 complexity/research qualification, adaptive coordination and optional range/defensive-transfer extensions.

These features are not claimed complete. T04–T10 are accepted within the enabled legacy/scripted scope. The broader Phase 0 upstream audit/qualification, live-model qualification in T11, T12–T19, and the full scientific study remain incomplete. Initial T14 reducers, planner-only T15 portions and basic T16 export/comparison are implemented.

## Implementation choices relative to the plan

- Service uses available Python 3.13.9 (supports 3.12+) while the engine stays on 3.8.11.
- The UI polls saved/live metadata and requests frames. The URL preserves replay context across refresh/reconnect. This works without an ephemeral WebSocket subscription; WebSockets can be added later without changing the run loop. Native checkpoint resumption is not implemented.
- Configuration/action schemas and their generated types are implemented. Full typed world/frame/message schemas remain a contracts extension; current engine wire validates envelope/version and the adapter constructs internal payloads.
- Transport messages forward immutable evidence IDs, and the engine checks their originating actor before extracting allowlisted address fields. It stores all engine evidence for a run. Native address flags are updated only on delivery.
- Worker reports explicitly include selected candidate actions and own technical knowledge. A coordinator can see only delivered reports, including those reported fields; it cannot read another actor's undisclosed memory or truth.
- Scripted retries at most twice per local unsuccessful action; no automated provider transport retry. A failed provider response or timeout ends the run as errored with usage conservatively reserved when unknown.
- Budget reservation uses UTF-8 bytes plus output cap and fixed framing allowance; local provider token counts settle usage. This is an admission guard, not a mathematical guarantee for every possible tokenizer. No live cost study was done.
- Researcher truth remains accessible to the human through the local UI and bundles, never to the cognitive inputs. The private graph omits inferred physical edges and uses observed-address labels when hostname is unknown.

## Before merging

Review the parent branch diff and the documented submodule patch. Validate any added profile/provider using development fixtures. Keep scientific qualification pending until the full pilot/frozen-study work is explicitly authorized. Do not merge based solely on a functioning UI.
