# Workbench implementation status

4 October 2026 — Phase 1–2 software acceptance completed for the enabled legacy/scripted profile, local branch `research-workbench`. [Per-ticket evidence](research/PHASE_1_2_ACCEPTANCE.md).

## Implemented

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

- Generic four-zone generator, network variation beyond the inherited scenario, qualified linear/branching/recovery families, and explicit generic zone-access policy.
- Qualified active defender and service-disruption mission. Monitor observes; it does not remediate.
- The full upstream regression suite and every exploit/escalation precondition, generic NACL/block/bandwidth semantics, inactive-session behavior in the inherited operational gate, and broad seed solvability/difficulty calibration. Fixed legacy scan/exploit disconnection and actor-local operational-gate boundaries are checked.
- Live Ollama/model verification, hosted providers, coordinator schema repair, evidence-preserving context summarization, pinned model digests, and provider seed/generalization studies.
- Batch job execution/resumption/retry manager and experiment-launch controls. The planner exports jobs only. No research experiments are run or scheduled.
- Final pairing by explicit replicate IDs, prespecified treatment interactions, missing/refused/technical-error outcome handling for final analysis, budget frontiers, and publication-quality plots.
- Adaptive coordination and optional separate CC4/range adapters (conditional research extensions).

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
