# Ordered implementation plan

This is a programmer handoff. Tickets specify deliverables and acceptance criteria; they are not claims of completed features. Dependencies are intentional: build visible, verifiable simulator behavior before paying for large LLM experiments.

Implementation checkpoint, 4 October 2026: **Phase 1 and Phase 2 (T04–T10)
are accepted for the enabled legacy enterprise profile with scripted/mock
cognition and passive/monitor defense**. See [the per-ticket acceptance evidence](PHASE_1_2_ACCEPTANCE.md).
Phase 3 and the scientific evaluation phases remain pending; acceptance does
not imply every upstream action or scenario is qualified.

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

### T11 LLM providers and resource enforcement

Implement one real provider, a configurable local provider interface, response validation, one bounded schema repair, cancellations/timeouts, prompt versioning, actual usage capture, and reservations for concurrent calls. Add keys through local secrets/settings; never export keys with artifacts.

Acceptance: hierarchy coordinator usage is counted; retries/repairs/summaries are charged; calls cannot be scheduled beyond reserved limits; actual usage differences are settled; invalid/refusal/provider errors are visible. Recorded decisions replay without contacting the provider. Exact model identity is recorded where available.

### T12 Four-zone research generator and reachability policy

Implement linear and branching templates with variable real layouts/services and declared access prerequisites, reusing CybORG technical objects. Turn off legacy hostname-specific gating in these generic profiles. Add the qualified recovery scenario afterward.

Acceptance: a legal scripted route reaches targets; denied shortcuts fail; services and escalation assumptions match engine implementation; scenario seeds vary more than labels/IPs; 1-8 supported workers validate. The materialized-world file captures every initial relevant condition. No model-specific tuning on held-out worlds.

### T13 Qualify defense and optional disruption mission

Use a fixed, named defender policy first. Validate restore/removal behavior and effects on all red actors. Add service-disruption objective only after Impact/service state are verified against privilege and knowledge assumptions; document any upstream simplification.

Acceptance: recovery actually changes session/state and objective metrics. A scheduled intervention is logged. A service-disruption mission fails when its prerequisites are unmet and succeeds only when the designated service state changes. Unsupported profiles remain disabled in UI/capabilities.

## Phase 4: Scientific evaluation

### T14 Metric reducers and fixture verification

Implement success, effort, actual usage, coordination cost, duplication, invalid-decision, communication, and termination metrics. Version formulas and save analyzer configuration.

Acceptance: hand-checked fixtures verify host deduplication, team-reward deduplication, invalid denominators, failure/censoring handling, and token accounting. Every metric is recomputable from saved artifacts. Lower behavioral diversity is not automatically displayed as better.

### T15 Batch scheduler and experiment builder

Implement deterministic matrix expansion, pairing by materialized-world ID, replicates, job/attempt IDs, limited concurrency, hard stop rules, cancellation, completed-job reuse, and technical-failure retries.

Acceptance: episode count matches preview; ordinary failures are never retried to success silently; stopping/restarting a batch preserves completed results and records partial attempts. UI and CLI produce the same experiment matrix. Closing the UI does not stop execution.

### T16 Comparative analysis and exports

Implement planned paired/clustered estimates, confidence intervals, budget frontiers, failure summaries, and scientific plots. Provide CSV, configs/worlds, event bundles, and analysis artifacts.

Acceptance: sample counts and filters are visible; technical failures/refusals/manual interventions are accounted for; pairing excludes mismatched worlds; repeated trials on one world are not treated as independent worlds. Exported plots/results reproduce from the run bundle.

### T17 Pilot, revise, and freeze

Run the 36-episode pilot after mock qualification, inspect trivial goals/deadlocks/information leaks/costs, revise on development worlds, then freeze policies/scenarios/prompts and pre-specify final analysis.

Acceptance: final suite has genuinely challenging legal missions, measurable coordination behavior, affordable budgets, and tested reproducibility. Final evaluated world IDs are separate from development IDs. Sample sizes are justified by precision/power, not only by a 50-trial target.

## Phase 5: Optional contribution and transfer

### T18 Adaptive policy and generalization

If the core results motivate a method, implement adaptive coordination using only observable signals. Evaluate against fixed hybrid/random switching and perform ablations. Add second-model, held-out size, and communication conditions.

Acceptance: switching cannot consult privileged truth; thresholds are frozen before evaluation; gains include total coordination cost and uncertainty. No claim of superiority is made if evidence does not support it.

### T19 Optional CC4/isolated-range backend

Only after the primary workbench is stable, implement a new adapter in a separate environment. Map semantics explicitly and keep result domains distinct. A CC4 defensive study is a transfer extension, not a silent replacement of the offensive paper.

Acceptance: adapter contract tests pass; action durations/observation/mission differences are disclosed; comparisons use comparable organizational metrics, not incompatible raw rewards.

## Handoff and completion checklist

A programmer's delivery is complete when the researcher can install from locks, configure both organizations without editing Python, inspect actual actions and knowledge, run/restart a planned batch, export evidence, and reproduce the metrics offline.

A researcher's study is complete only after literature verification, pilot qualification, frozen final experiments, uncertainty/generalization analysis, and a clear new result. A finished UI alone does not fulfill the paper.

First useful milestone: T01-T06 yields a configurable, visible enterprise laboratory with scripted actions and replay. Second: T07-T11 yields real hierarchy/swarm LLM teams. Third: T12-T17 yields the research evaluation workbench. T18-T19 are conditional extensions.

Avoid calendar estimates until T01-T03 establish compatibility and T11 measures actual provider cost. Track acceptance criteria and qualified behavior instead of promising a top-conference result by a date.
