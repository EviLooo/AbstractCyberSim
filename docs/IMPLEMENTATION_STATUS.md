# Workbench implementation status

3 October 2026 — first runnable system, local branch `research-workbench`.

## Implemented

| Area | Delivered behavior |
| --- | --- |
| Repository | Existing AbstractCyberSim remote; implementation branch from main; pinned CybORG submodule; two-line actor-owned Portscan lookup patch; separate runtime locks. |
| Contracts | Strict schema-1.0 configuration/action/experiment models; checked-in JSON Schemas; generated TypeScript config types; API/CLI validation. Design examples remain separate. |
| Native adapter | Fresh enterprise Scenario2 generation per run, 1–8 independently owned worker sessions, external Sleep defaults, passive/monitor presets, discovery/scan/exploit/escalation catalog, invalid-action rejection. |
| Privacy | Known=True native parameters only; own sessions/cache; separate truth channel; private observations/history/inboxes; engine-proven address/hostname intel; no port/session grants. |
| Organizations | Hierarchy star report/assignment pipeline and bootstrap waiting; swarm local claims/tie-breaking; independent baseline; per-worker and neutral team-cap-one scheduling. |
| Communication | Recipient-copy envelopes, tick+1+delay delivery, seeded loss, bytes/envelope caps, TTL and delivery status logs. Explicit overlay. |
| Cognition | Deterministic scripted baseline; optional Ollama structured provider, serial conservative reservations, actual/unknown usage accounting, worker format repair, saved transcripts. No live provider call made. |
| Controls/storage | Initialize paused; single joint tick; run/pause at tick boundaries; stop; four-live-world cap; SQLite index; config/world/manifest/events/frames; restart marks native state interrupted; offline replay. |
| UI | Configuration editor/import/export/JSON; actual network and organization graphs; selected-worker view; host/worker/coordinator inspector; attempted/native/concrete actions and TRUE/FALSE/UNKNOWN; message timeline; saved-frame replay; manual actions flagged. |
| Planning/evaluation | Matrix validation/preview/export; deduplicated controlled/privileged hosts and targets; attempts/invalid/duplicate/message/usage reducers; ZIP and CSV exports; descriptive paired success comparison with exclusions and world clustering. |

## Checked

`pytest -q`: 18 passed. Checks execute bounded technical fixtures in pytest temporary directories and never call a live model. They are not hypothesis experiments. Native discover/scan/exploit paths are checked for 1, 2, 4, and 8 workers. Shared evidence is rejected for a forged sender; accepted evidence creates address knowledge but neither scan caches nor sessions. Mocked provider checks verify charged format repairs, admission without an over-budget call, and conservative accounting for unknown usage after a transport failure.

`npm run build --prefix frontend`: generated contracts type-check and the production application builds. In-app browser verification covers idle startup, configuration controls, matrix preview, planner navigation, and visualization/replay of archived software-test fixtures served from their temporary directory. User data store starts empty.

The upstream CybORG acceptance API module also passes: 7 passed, 1 skipped. It covers the original single-Red scenario interfaces. Its existing Python/Gym deprecation warnings remain.

## Pending from the full research design

- Generic four-zone generator, network variation beyond the inherited scenario, qualified linear/branching/recovery families, and explicit generic zone-access policy.
- Qualified active defender and service-disruption mission. Monitor observes; it does not remediate.
- The full upstream regression suite beyond the checked API module, every exploit/escalation precondition, full unreachable/blocked-route qualification, and calibration of scenario solvability and difficulty.
- Live Ollama/model verification, hosted providers, coordinator schema repair, evidence-preserving context summarization, pinned model digests, and provider seed/generalization studies.
- Batch job execution/resumption/retry manager and experiment-launch controls. The planner exports jobs only. No research experiments are run or scheduled.
- Final pairing by explicit replicate IDs, prespecified treatment interactions, missing/refused/technical-error outcome handling for final analysis, budget frontiers, and publication-quality plots.
- Adaptive coordination and optional separate CC4/range adapters (conditional research extensions).

These features are not claimed complete. In the original ticket plan, this release substantially implements T01–T10, the local-provider path of T11, the initial reducers of T14, planner-only portions of T15, and basic export/comparison of T16. It does not complete all acceptance criteria of those tickets or T12–T19.

## Implementation choices relative to the plan

- Service uses available Python 3.13.9 (supports 3.12+) while the engine stays on 3.8.11.
- The UI polls saved/live metadata and requests frames. This supports reconnect without depending on an ephemeral WebSocket subscription; WebSockets can be added later without changing the run loop.
- Configuration/action schemas and their generated types are implemented. Full typed world/frame/message schemas remain a contracts extension; current engine wire validates envelope/version and the adapter constructs internal payloads.
- Transport messages forward immutable evidence IDs, and the engine checks their originating actor before extracting allowlisted address fields. It stores all engine evidence for a run. Native address flags are updated only on delivery.
- Worker reports explicitly include selected candidate actions and own technical knowledge. A coordinator can see only delivered reports, including those reported fields; it cannot read another actor's undisclosed memory or truth.
- Scripted retries at most twice per local unsuccessful action; no automated provider transport retry. A failed provider response or timeout ends the run as errored with usage conservatively reserved when unknown.
- Budget reservation uses UTF-8 bytes plus output cap and fixed framing allowance; local provider token counts settle usage. This is an admission guard, not a mathematical guarantee for every possible tokenizer. No live cost study was done.
- Researcher truth remains accessible to the human through the local UI and bundles, never to the cognitive inputs. The private graph omits inferred physical edges and uses observed-address labels when hostname is unknown.

## Before merging

Review the parent branch diff and the documented submodule patch. Validate any added profile/provider using development fixtures. Keep scientific qualification pending until the full pilot/frozen-study work is explicitly authorized. Do not merge based solely on a functioning UI.
