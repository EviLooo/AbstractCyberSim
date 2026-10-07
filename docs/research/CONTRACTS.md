# Implementation contract definitions

For the next bounded research profile, use
[the revised contract/interface handoff](REVISED_GRADUATION_PLAN.md#10-architecture-and-programmer-interfaces).
Its proposed diagnostic, explicit-method, artifact/token and evidence contracts
require a new explicit runtime version; they do not currently exist. Old
schema-1.0 configs and replay semantics stay unchanged. This document's original
design contracts remain historical guidance where they agree with that handoff.

These are language-neutral version-1 contract requirements. Implement JSON Schemas and generate Python/TypeScript types from them in T02. The examples use `0.1-design` until an implementation supplies validated runtime contracts. Treat new required fields or changed meanings as a schema-version change.

## Configuration and resolved world

`EpisodeConfig` contains the nested fields illustrated in `examples/*.episode.json`. Registry-specific parameters are checked against that registry entry's schema; unknown parameters are rejected. `coordinator_prompt` may be carried as a shared preset reference in swarm but is unused; the resolved config marks that explicitly. Policy-specific defaults are replaced when a batch changes architecture, not inherited from a different policy.

`ResolvedEpisode` contains config hash, original config, resolved registry entries and prompt hashes, total worker/reasoner counts, materialized world ID/hash, native seed, and resolved communication graph. Model and scenario versions may not remain unresolved placeholders when a real run is created.

`WorldSpec` contains:

| Field | Type and meaning |
| --- | --- |
| `world_id`, `schema_version`, `profile_id`, `profile_version` | Stable strings. |
| `world_seed` | Integer used only for generation. |
| `hosts` | Host descriptions: IDs, OS/user/process/service templates, interfaces/links, roles, and values. Privileged. |
| `subnets` | IDs, CIDRs, membership, and declared routing-policy parameters. Privileged unless exposed in mission/observation. |
| `physical_edges` | Host/interface endpoint pairs with deterministic IDs; connectivity, not an assumed unrestricted service path. |
| `actors` | Native ID, team ID, action catalog ID, starting-session specifications, initial observation policy, and default policy. |
| `initial_access` | Qualified controlling-session type, owner, username/privilege, entry host, and parent relations. |
| `objective` | Evaluator ID/version and target host/service IDs. Privileged matching criteria. |
| `mission_brief` | Agent-public goal text/known asset descriptors; never the complete hidden IP/service inventory. |
| `defender`, `green`, `scheduled_events` | Policy versions and parameters needed to reproduce the world. |
| `qualification_id` | Engine/profile revision against which legality/solvability tests passed. |

World IDs are hashes of normalized technical initial conditions, including actor resources. Hierarchy and swarm can share a world ID because the cognitive coordinator/communication graph lives above native state. Changing worker count normally produces a different world ID, because actor/session resources change. Separately retain an underlying network-instance ID to analyze the same network across counts.

`ExperimentPlan` expands named factors and policy defaults. Use `world_id`, worker count, transport condition, model identity, and replicate as pairing keys where those factors vary. The example has one fixed model, so model need not appear explicitly in its pair key. `replicate` determines provider/simulation seed derivation; it does not regenerate a different technical world.

## Observations and knowledge

`ObservationDelta`: schema version, run ID, tick, actor ID, evidence ID, native outcome enum (`TRUE|FALSE|UNKNOWN`), and normalized observed host/interface/process/session fields. Native action results may be empty; this is not evidence of success. Include source action ID if applicable.

`AgentView`: reasoning-agent ID, native actor ID if any, mission brief, own observations/memory, delivered message IDs, acknowledged task/claim state, eligible action descriptors, and remaining budget allocation. No raw WorldSpec, truth snapshot, false native action-space keys, or undisclosed peer views.

`KnownFact`: fact ID, subject, field/value, first/last observation ticks, origin actor/evidence ID, status (`self_observed|peer_reported|confirmed|stale`), and optional corroborating references. Derived facts require their evidence IDs. Confidence is not a substitute for native authorization.

`VerifiedIntelDelivery`: message ID, recipient actor, allowlisted address/hostname observation fragment, evidence IDs, sender authorization proof/reference, and delivery tick. Constructed only by the transport/evidence verifier. The engine updates known-parameter flags; it does not import port caches, privileges, session identities, or arbitrary claims.

## Actions and decisions

`ActionDescriptor`: registered action ID/version, display name, required parameter types, compatible session kinds, permitted observed targets/parameters, documented simulated effects, and evidence requirements. The UI renders the same descriptions used in the prompt catalog.

`ActionProposal`: proposal ID, worker ID, native actor binding, tick, action ID, parameter dictionary, task/claim reference, evidence IDs, declared rationale summary, and outgoing message drafts. Worker identity/actor binding come from the runner, not free-form model data.

`ValidatedAction`: proposal reference, actor ID, translated native action ID/parameters, gateway validation outcome, neutral scheduler eligibility, and rejection category if relevant. A gateway-valid proposal may still fail technically in the engine.

`JointAction`: tick plus a complete map from each externally controlled native actor to one validated action or explicit Sleep. Do not send several actions for one actor in one tick. A future engine with action durations needs a backend-specific readiness field rather than pretending it has identical timing.

`StepResult`: tick, per-actor observation deltas, requested/native executed action records, actual execution order where available, native invalid replacements, termination status, and one reward breakdown per team. Privileged truth/mission score is a separate channel. Record abstract and concrete sub-action details when available, without revealing hidden causes to policies.

## Messages, tasks, and claims

`MessageEnvelope`: ID, sender, same-team recipients, kind, creation tick, extra delay/derived delivery tick, TTL, evidence references, payload, UTF-8 serialized payload/envelope byte count, and delivery status per recipient copy. Use a canonical encoding for reproducible capacity calculations.

`TaskAssignment`: task ID, assigning coordinator, worker, objective/known-target descriptor, allowed action family, completion condition, priority, issue tick, expiry tick, and delivered/acknowledged/completed status. Unknown target addresses cannot be introduced without authorized evidence.

`PeerClaim`: claim ID, sender, target/action-family task key, priority, evidence, issue/expiry tick, received competitor IDs, and local tie-break outcome. A claim is not a globally enforced lock. Log collisions rather than secretly eliminating them.

Transport state includes declared graph/version, in-flight queues, used capacity, seeded loss outcomes, and per-message events. Native cyber bandwidth and research message capacity are different units/mechanisms.

## Events, snapshots, and summary

`RunEvent` required fields: schema version, run ID, increasing sequence, tick, type, wall timestamp, visibility, and payload. Optional typed references: actor, decision, action, task, message, evidence, provider request. Event types include run_started, message_enqueued/delivered/dropped/expired, intel_ingested, task_assigned/acknowledged/expired, claim_created/collided, decision_requested/completed/invalid, action_proposed/selected/rejected/executed, observation_received, snapshot_saved, budget_reserved/settled/exhausted, run_paused/resumed/stopped, engine_error, provider_error/refusal, and run_finished.

`WorldSnapshot`: tick, host/service state, native sessions with owner and privilege, physical links/policy constraints, and mission truth. Store separately from policy-facing observations. UI host classification is derived from these fields, not from worker declarations.

`EpisodeSummary`: run/config/world/network-instance IDs, job/attempt/replicate IDs, engine/application/prompt/provider versions, outcome, stop tick, success tick or null, per-team usage/cost, per-action effort, communication/duplication/invalid metrics, manual intervention flag, metric versions, and technical errors. Preserve unavailable usage/pricing as null, never zero.

## State transitions and errors

Run lifecycle: created -> preflight -> initializing -> ready -> running; running may enter pausing -> paused -> running, or stopping -> stopped; normal termination enters finalizing -> finished. Initialization/engine failure enters failed with a recorded error. Only valid transitions are accepted; duplicate commands are idempotent where applicable. A replay view is not an executing run.

Machine-readable errors include unknown_schema, invalid_config, unimplemented_capability, unqualified_scenario, unsupported_team_size, unknown_model, provider_unavailable, provider_refusal, malformed_decision, unauthorized_parameter, unverified_evidence, invalid_native_action, engine_exception, protocol_timeout, exhausted_budget, illegal_run_transition, and manual_intervention_disallowed.

Distinguish errors exposed to agents from detailed researcher diagnostics. Hidden failure causes, topology, session maps, or vulnerability details must not leak through a richly worded validation error. An agent can receive a generic invalid/action-failed outcome with only causes supported by its existing evidence; the full recorder stores the detailed reason.

Use stable clock/seed/ID namespaces; sort serialized dictionaries for hashing but preserve execution/message order explicitly. A configuration hash identifies settings; world hash identifies actual initial conditions; run ID identifies one attempt. These are not interchangeable.
