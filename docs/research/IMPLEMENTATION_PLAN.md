# Ordered implementation plan

**5 October 2026 scope revision:** [the revised graduation handoff](REVISED_GRADUATION_PLAN.md)
is authoritative for remaining work and ordering. It requires a small diagnostic,
credential/capability and patch/recovery profile; explicit techniques and the
bounded credential model are promoted from optional T13b. Its R1–R7 gates replace
the broader next-step ordering below. Full isolate/unisolate, generic graphs,
continuous multi-effect defense and range transfer are explicitly deferred with
reasons. Existing ticket/acceptance history below is preserved. No implementation,
new simulations, research experiments or live LLM calls accompanied this revision.

**Next: R1, a paired evidence-dependent diagnostic fixture**, followed by R2
capability/credential qualification. A broad seed sweep of the old repeated-workflow
profile would measure its limitations but would not implement the missing choices.
See [source and requirement coverage](PLAN_SOURCE_AUDIT.md) and
[the completion ledger](COMPLETION_LEDGER.md). Do not read historical optional
labels or broad requirements below as the new graduation scope.

Latest bounded checkpoint: [observed search and wider route qualification](OBSERVED_SEARCH_ACCEPTANCE.md)
adds T12f search and selected T12b/T13a composition checks. Review the
[completion ledger](COMPLETION_LEDGER.md) for open requirements before advancing;
this checkpoint does not close Phase 3 or authorize experiments/live calls.

This is a programmer handoff. Tickets specify deliverables and acceptance criteria; they are not claims of completed features. Dependencies are intentional: build visible, verifiable simulator behavior before paying for large LLM experiments.

Implementation checkpoint, 4 October 2026: **Phase 1 and Phase 2 (T04–T10)
are accepted for the enabled legacy enterprise profile with scripted/mock
cognition and passive/monitor defense**. See [the per-ticket acceptance evidence](PHASE_1_2_ACCEPTANCE.md).
Phase 3 and the scientific evaluation phases remain pending; acceptance does
not imply every upstream action or scenario is qualified.

Phase 3 checkpoint: the isolated CC4 adapter, temporal evidence modules and
the first bounded **T12b segmented route profile** are implemented. See
[route semantics and acceptance](ROUTE_COMPLEXITY_ACCEPTANCE.md). This includes
native source ACLs and an explicit privileged pivot deployment extension,
not a fully calibrated cyber environment. **Bounded T12d sustained mission
primitives and deadlines are now implemented**; see [mission acceptance](MISSION_COMPLEXITY_ACCEPTANCE.md).
The bounded **T12f baseline/diagnostic checkpoint** is also implemented; see
[policy and fixture acceptance](BASELINE_DIAGNOSTICS_ACCEPTANCE.md). **T11 live-model
qualification and wider scenario calibration remain open** before research experiments.
The missing bounded **T12b route-tradeoff extension is now implemented**; see
[exact semantics and qualification](ROUTE_TRADEOFFS_ACCEPTANCE.md) and the
[requirement-by-requirement completion ledger](COMPLETION_LEDGER.md). Explain
any proposed deferral and its effects to the researcher before moving on.
This checkpoint does not close all of T12b or Phase 3.

Research revision, 4 October 2026: **hierarchy versus swarm LLM attacker teams
remains the primary comparison**. The environment must expose meaningful
reasoning, adaptation and coordination demands; rule-based/planner and single
LLM baselines diagnose when those demands matter. The static legacy fixture is
software acceptance, not a sufficient final research environment. Phase 3 now
follows [the modular complexity design](ENVIRONMENT_COMPLEXITY_DESIGN.md), with
separate complexity knobs, native qualification and behavioral validity gates.

## Phase 0: Foundation and qualification

### T01 Pin the engine and preserve current work

Export the working conda/pip versions and record the inspected upstream hash. Keep the existing CybORG checkout and its untracked experiments/virtual environment intact. Establish a small engine fork or reviewed patch path and parent-repository dependency registration; do not silently overwrite local files or publish upstream changes.

Apply the reviewed two-line Portscan fix and include a multi-actor regression. Audit the exact primary actions for other assumptions about `Red`, `Blue`, session types, reward names, and legacy labels.

Acceptance: clean setup from documented locks; 1/2/4 red actors can discover, scan, and acquire independently owned sessions; original single-Red behavior still works; upstream diff contains only explained compatibility changes. Existing action/API tests appropriate to the patch pass. Test no route, missing session, and invalid target without a crash.

### T02 Establish contracts and the process bridge

Implement versioned JSON contracts, generated types, serializer, bounded request/response framing, startup capability handshake, timeouts, and child cleanup. Keep engine-specific Python 3.8 code apart from modern service code.

Acceptance: a modern service process can launch the engine, create/reset a fixed world, submit one joint action, receive per-actor observations and one team score, request a privileged snapshot, and close cleanly. Unknown versions/fields are rejected. Library warnings never corrupt protocol stdout.

### T03 Materialize the legacy enterprise baseline

Construct a programmatic scenario using audited enterprise templates. Add named red workers, individual initial sessions, explicit team mappings, externally driven SleepAgent defaults, fixed Blue/Green presets, and an independent objective evaluator. Avoid relying on FileReader's one-agent-per-team assumptions for research scoring.

Acceptance: fixed seed/materialized-world reset returns the same initial graph/services/footholds; separate fresh episodes do not retain calculator or agent memory state. Team score counts a target once, even when two workers own sessions on it. Mission success requires actual qualifying target access.

## Phase 1: Visible engine and researcher workflow

### T04 Build the local service, run record, and neutral episode loop

Implement create/start/pause/single_tick/continue/stop, state transitions, SQLite run metadata, append-only events, truth snapshots, and explicit termination reasons. The same engine loop is callable from a CLI and API.

Acceptance: each tick sends one joint-action map; two workers do not cause two defender turns. Missing actions become declared Sleep, not an undocumented internal policy. Disconnect/reconnect restores UI event position. Pausing and display speed do not change outcomes for scripted decisions.

### T05 Build the first interactive network view

Render actual host/subnet links and session/privilege changes. Add click-to-inspect hosts and an action timeline showing preconditions, attempted action, actual result, and state delta. Provide researcher-truth versus selected-agent view with a prominent label.

Acceptance: all nodes/edges/statuses come from saved/live engine data; no demo animation determines outcomes. A scripted scan/exploit visibly discovers a host then adds the corresponding session. UNKNOWN and FALSE remain distinct. Replay works with no provider calls.

### T06 Implement the setup editor and configuration round trip

Schema-driven fields for scenario, worker count, policy, seeds, budgets, communication, and model preset. Save/import/export configurations and show resolved settings before run creation. Show supported ranges and reject impossible settings.

Acceptance: UI save/load preserves configuration semantics; exporting then running via CLI uses identical resolved settings. Changing worker count affects actors/sessions but not host count. Running mode/count edits create a new run. Exploration interventions are visibly labeled and logged.

## Phase 2: Real organizational behavior

### T07 Observation encoding, private memory, and action gateway

Implement evidence IDs, native outcome normalization, allowed-value filtering, private fact/report distinctions, verified-address intel delivery through `AgentInterface.update`, structured proposals, actor-bound action construction, and validity failures.

Acceptance: no false action-space keys or privileged data in prompts; new observations preserve prior private knowledge; one worker cannot use another's sessions. An undelivered or unsupported claim cannot unlock a target; delivered verified IP evidence makes scanning eligible, but cannot populate native exploit caches or create sessions. Abstract reverse-shell/controller limitations are validated. Injected invalid decisions cannot escape the action catalog.

### T08 Research communication transport

Implement sender/recipient envelopes, star/mesh/sparse graphs, tick delay, seeded loss, per-team delivery bytes/envelopes, overflow/TTL events, and scheduled link interruption.

Acceptance: same-tick delivery is impossible; adversaries never receive team messages; delivered/dropped/expired counts reconcile; broadcast charges recipient copies; a leader sees only delivered reports. Known loss seeds reproduce mock-run delivery history.

### T09 Mock providers and distinct policy implementations

Implement hierarchy assignments/reporting and decentralized worker claims/tie-breaks. Use scripted/mock cognition to establish different policies cheaply. Swarm workers receive only their individual views/inboxes; no shared blackboard or allocator.

Acceptance: on a branching fixture hierarchy assigns distinct tasks, swarm independently proposes/claims tasks, and their event traces differ. A message-loss fixture causes different information availability and observable duplicate/idle behavior. Both obey identical budgets and tool schedules. A policy cannot query global truth.

### T10 Team communication visualization

Add team graph, assignments/claims, worker/coordinator inspector, message trails, delayed/lost delivery, and private-knowledge selectors. Show worker count separately from total reasoner count.

Acceptance: displayed topology matches actual transport behavior; the leader's view changes only on delivery; selecting a node or timeline position never changes decisions. The researcher can explain one complete mission using visual evidence.

## Phase 3: LLM cognition and qualified research scenarios

**Backend gate before T12:** [the completed CC4 compatibility audit](CC4_COMPATIBILITY_AUDIT.md)
supports adding an isolated CC4 adapter and production research generator before
extensively rebuilding the legacy engine. Nine bounded fixtures pass, including
1/2/4/8 external workers, cross-zone ownership, intelligence delivery and native
restore/block/allow effects. They do not close T12/T13 or qualify the full study.
Preserve the accepted legacy backend; complete the adapter/privacy/reset/mission/
replay gates in the audit before enabling CC4. Reuse qualified CC4 durations and
defense mechanisms in T12/T13 rather than rebuilding them in the old engine.

Implementation checkpoint: [the isolated CC4 adapter is now selectable](CC4_ADAPTER_ACCEPTANCE.md).
Ownership, privacy, reset/pairing, native durations, controlled-service missions,
bounded restore response and artifacts are checked. This closes the initial
adapter gate in that scope, not T12/T13 or arbitrary-size/complexity qualification.

### T11 LLM providers and resource enforcement

Implement one real provider, a configurable local provider interface, response validation, one bounded schema repair, cancellations/timeouts, prompt versioning, actual usage capture, and reservations for concurrent calls. Add keys through local secrets/settings; never export keys with artifacts.

Acceptance: hierarchy coordinator usage is counted; retries/repairs/summaries are charged; calls cannot be scheduled beyond reserved limits; actual usage differences are settled; invalid/refusal/provider errors are visible. Recorded decisions replay without contacting the provider. Exact model identity is recorded where available.

### T12 Modular research environment — implement in the following substeps

Implementation checkpoint: [modular settings and temporal evidence](TEMPORAL_COMPLEXITY_ACCEPTANCE.md)
now delivers portions of T12a/T12c/T12e on CC4: a strict additive contract,
capability registry and deterministic manifest compiler; delayed private
host/service evidence, timestamps/history/conflicts, local refresh/replanning
and saved observable recovery. Native recovery is integrated with this layer.
The full generic compiler, static routes/dependencies, mission dwell and broader
module qualification remain pending; these tickets are not closed wholesale.

Detailed interfaces, repository paths, knobs, episode example and evidence are
in [ENVIRONMENT_COMPLEXITY_DESIGN.md](ENVIRONMENT_COMPLEXITY_DESIGN.md). These
are planned features; current runtime schema-1.0 and legacy behavior stay intact.

**T12a — profile contract, registry and compiler.** Introduce explicit versioned
research-profile contracts, dependency checks, module capabilities, immutable
presets and a config-to-native-world compiler. Store resolved module versions,
seed namespaces, physical inputs, schedules, mission and split separately from
the organizational treatment. Provide a legacy adapter, not silent changes to
old config semantics. The design-only v2 example must not run as schema-1.0.

Acceptance: unsupported module/combinations fail before engine launch; preset
round trip resolves identical inputs; world generation never reads model or
architecture; disabled modules are no-ops with no unrelated RNG consumption;
fresh episode resets module state; all old schema/mission fixtures still pass.

**T12b — static physical complexity and meaningful actions.** First qualify
CC4's existing enterprise zones and templates through the research generator,
with alternative paths, service/privilege diversity and explicit native
source/session/service reachability. This does not qualify arbitrary zone counts.
Then add generic linear/branching profiles with bounded dead ends only when
needed and separately qualified. Replace the legacy inherited hostname gate only
inside generic profiles. Adapter route checks and native effects must agree.
Keep high-level action selection clearly labeled; do not claim LLM vulnerability
selection while native ExploitRemoteService chooses its sub-action.

Acceptance: legal observation-driven trajectories reach targets; blocked or
unowned shortcuts fail; patched/incompatible templates fail the affected native
technique; seeds vary actual routes/services/dependencies; supported worker
counts qualify; all initial inputs are materialized. A larger host count alone
does not qualify a reasoning scenario.

**T12b route-tradeoff extension:** materialize fast exposed SSH, slower quieter
FTP and optional root-service gateways using independent seed streams. Configure
native exploit durations and a separately labeled traffic sensor with bounded
temporary native service ACL quarantine. Disclose limited service assessments
only after successful own scans or verified delivery; never disclose ACLs or
guaranteed success. UI controls and saved effects must match native execution.
Acceptance includes actual user/root sessions, changed tick costs/deadline
outcomes, denied incoming/outgoing traffic and release, privacy/delay/cache
boundaries, deterministic resets and matched organizational worlds.
[Implemented scope and remaining requirements](ROUTE_TRADEOFFS_ACCEPTANCE.md).
Credential routes require the separate T13b model; service quarantine does not
close full isolate/unisolate or patch semantics.

**T12c — time-stamped observations and beliefs.** Add evidence age, report source,
contradiction/unconfirmed status, bounded observation delay and legal refresh
actions. Preserve historical facts while distinguishing current native access.
Defender and attacker projections remain separate. No failed action gains an
omniscient cause label; no hidden event silently refreshes policy knowledge.

Acceptance: hidden-state perturbation leaves prompts/candidates unchanged until
disclosure; stale reports cannot restore sessions/cache; a fresh scan can reveal
a qualified service change; old/new evidence is inspectable without erasing
history. A controller's loss is visible only through the declared status model.

Checkpoint: consecutive simultaneous holds, inclusive deadlines and live host
prerequisites are delivered; native restoration and legal recovery are checked.
Generic dependency/action primitives, broad seed solvability and prespecified
sequential/parallel opportunity diagnostics remain unqualified.
[Exact bounded acceptance](MISSION_COMPLEXITY_ACCEPTANCE.md).

**T12d — multi-target mission and recovery opportunities.** Implement physical
objective/dependency primitives and optional consecutive access dwell/deadline
conditions. Dependency edges refer to actual technical prerequisites, not labels
in reports. Provide legitimate alternative paths and bounded intervention rates.
Reject or label worlds with no feasible recovery; do not auto-grant access.

Acceptance: report text cannot satisfy objective; loss of access resets dwell;
defense continues through dwell; sequential versus parallel opportunity is
measurable in a manifest; failures remain recorded/censored. Reference fixtures
establish positive and denied paths using legal observed actions.

**T12e — researcher controls and event visualization.** Add qualified C0–C3
presets and module controls driven by capabilities. Display exact resolved
values, composition restrictions, stale knowledge, blocked access, actual
defense effects and mission dependencies/dwell. UI, JSON and CLI share config;
presets can be expanded and customized. Unsupported knobs stay disabled.

Acceptance: researcher truth and worker-visible symptoms differ correctly;
replay reconstructs events without engine/model calls; initialize stays paused;
editing complexity creates a new run; exploration changes retain intervention
flags. UI animation never determines an effect.

Checkpoint: local rules and observed-frontier replanning, shared deterministic
state facts, private decision UI, offline diagnostics and bounded C0/C1/C2
development fixtures are delivered. Single/independent live LLM controls and
broad calibrated scenario qualification remain pending.
[Exact software acceptance](BASELINE_DIAGNOSTICS_ACCEPTANCE.md).

**T12f — diagnostic baselines and structural qualification.** Add frozen
local-information rule and replanning/search policies, single LLM and independent
worker controls, sharing observation/action filters and resource rules. Separate
a deterministic state tracker from a strategic planner. Qualify C0, C1 and C2
with bounded software fixtures before a live development pilot.

Acceptance: branching and recovery produce explainable nontrivial decisions and
distinct organization traces; scripts can succeed on control conditions;
baseline retries/refresh rules are documented and not deliberately crippled;
neither policies nor candidate generation consult hidden world plans. No minimum
LLM superiority is an environment acceptance criterion.

### T13 Active defense and optional operational extensions

**T13a — bounded recovery and reactive defender** (needed alongside T12c).
First qualify Remove/Restore on all registered red actors and affected native
registries/caches. Then add explicit isolate/unisolate and version-specific
patch transitions only after native consistency checks. Implement open-loop
scheduled conditions separately from a named defender that observes, investigates
and responds using bounded sensor coverage, reaction delay, budget and cooldown.
Pin event phases and native priorities. Do not count Monitor as active response.

Acceptance: actual routes/services/sessions and mission metrics change;
suspicious-PID/session prerequisites are honored; defender has no true compromise
inventory; its signal/decision/effect timestamps are logged; stale worker beliefs
remain stale until legitimate disclosure; no intervention singles out an
architecture label. Same reactive policy can produce different traces under
different attacker behavior; scheduled events are independently materialized.

**T13b — optional action/operational complexity.** After the core C0–C3 profile,
qualify explicit selection among existing native exploit techniques, decoys,
multi-tick action durations, benign user activity and business-service objectives.
Credential/re-entry models require separate native extensions, not invented
UI effects. Add service disruption only after Impact semantics are checked.

Acceptance: technique choices use observed prerequisites and never promise
success; busy workers cannot double-act and the defender still advances once;
false signals/decoys have provenance and bounded rules; normal user activity does
not silently spawn attacker access; disruption reflects real native service
state. Unsupported combinations remain disabled.

## Phase 4: Scientific evaluation

### T14 Metric reducers and fixture verification

Implement success, effort, actual usage, coordination cost, duplication, invalid-decision, communication, and termination metrics. Version formulas and save analyzer configuration.

Add evidence-age/refresh, observable disruption-to-valid-progress latency,
claim/assignment revision, blocked-route retries, access loss/recovery, target
dwell and defender reaction reducers. Separate hidden event time from observable
signal time; rationale text is not evidence of a causal reasoning mechanism.

Acceptance: hand-checked fixtures verify host deduplication, team-reward deduplication, invalid denominators, failure/censoring handling, and token accounting. Every metric is recomputable from saved artifacts. Lower behavioral diversity is not automatically displayed as better.

### T15 Batch scheduler and experiment builder

Implement deterministic matrix expansion, pairing by materialized-world ID, replicates, job/attempt IDs, limited concurrency, hard stop rules, cancellation, completed-job reuse, and technical-failure retries.

Expand resolved complexity modules as declared factors, not a black-box
difficulty number. Support one-factor ablations and selected interactions before
large sweeps; include profile/module/split hashes in pairing and exports.

Acceptance: episode count matches preview; ordinary failures are never retried to success silently; stopping/restarting a batch preserves completed results and records partial attempts. UI and CLI produce the same experiment matrix. Closing the UI does not stop execution.

### T16 Comparative analysis and exports

Implement planned paired/clustered estimates, confidence intervals, budget frontiers, failure summaries, and scientific plots. Provide CSV, configs/worlds, event bundles, and analysis artifacts.

Acceptance: sample counts and filters are visible; technical failures/refusals/manual interventions are accounted for; pairing excludes mismatched worlds; repeated trials on one world are not treated as independent worlds. Exported plots/results reproduce from the run bundle.

### T17 Pilot, revise, and freeze

After T12/T13 software qualification, prepare a behavioral evidence dossier for
each module: intended cyber process, assumptions, source mapping, expert review,
sensitivity ranges and optional isolated-lab transition comparison. Software
tests qualify implementation, not empirical realism. Describe the ABM entities,
states, observations, scheduling and submodels using ODD-style documentation.

Then run an explicitly authorized development pilot across resolved complexity
cells and diagnostic baselines; the earlier 36-episode organization-only example
is only a planning illustration. Inspect saturation, deadlocks, infeasible
recovery, information leaks and costs. Freeze modules, policies, prompts and
analysis before evaluating held-out service/path/event combinations and sizes.

Acceptance: legal missions expose measurable adaptation/coordination demands;
the suite is neither all instant successes nor all unrecoverable losses; causal
claims have ablations; behavioral assumptions have evidence levels; no test cell
is selected because an LLM or favored organization wins. Final world IDs are
separate from development; sample size follows precision/power and pilot cost.

## Phase 5: Optional contribution and transfer

### T18 Adaptive policy and generalization

If the core results motivate a method, implement adaptive coordination using only observable signals. Evaluate against fixed hybrid/random switching and perform ablations. Add second-model, held-out size, and communication conditions.

Acceptance: switching cannot consult privileged truth; thresholds are frozen before evaluation; gains include total coordination cost and uncertainty. No claim of superiority is made if evidence does not support it.

### T19 Optional defensive-transfer/isolated-range study

Only after the primary workbench is stable, implement any additional range adapter
in a separate environment. Map semantics explicitly and keep result domains
distinct. The offensive CC4 adapter is now the pre-T12 backend gate, not delayed
until T19. A separate CC4 defensive study remains a transfer extension, not a
silent replacement of the offensive paper.

Acceptance: adapter contract tests pass; action durations/observation/mission differences are disclosed; comparisons use comparable organizational metrics, not incompatible raw rewards.

## Handoff and completion checklist

A programmer's delivery is complete when the researcher can install from locks, configure both organizations without editing Python, inspect actual actions and knowledge, run/restart a planned batch, export evidence, and reproduce the metrics offline.

A researcher's study is complete only after literature verification, pilot qualification, frozen final experiments, uncertainty/generalization analysis, and a clear new result. A finished UI alone does not fulfill the paper.

Current milestone: T04–T10 supplies the accepted legacy/scripted foundation.
Next: T12a/T12b supplies modular static worlds; T12c/T12d/T13a supplies adaptation
and reactive defense; T12e/T12f/T11 supplies inspectable, qualified LLM team
comparisons. T14–T17 supplies behavioral validation and the frozen research
evaluation. T13b/T18/T19 are extensions with separate qualification.

Avoid calendar estimates until T01-T03 establish compatibility and T11 measures actual provider cost. Track acceptance criteria and qualified behavior instead of promising a top-conference result by a date.
