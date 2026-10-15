# Modular complexity and behavioral validity

**Scope superseded, 5 October 2026:**
[the revised graduation plan](REVISED_GRADUATION_PLAN.md) selects three interacting
mechanisms and bounded recipes from this broader design. Its mechanism
specifications, supported controls, R1–R7 milestones and explicit deferrals govern
future work. C0–C4 below remain exploratory historical bundles, not calibrated
difficulty. Full isolation, arbitrary graphs, broad operational features and
range transfer are optional; a small credential/explicit-technique/patch subset
is now core. No proposed capability becomes implemented through this revision.

Design revision: 4 October 2026. Programmer handoff for Phase 3; **proposed,
not fully implemented or scientifically validated**. Both legacy and CC4
adapters are selectable. The [temporal-module checkpoint](TEMPORAL_COMPLEXITY_ACCEPTANCE.md)
delivers an additive schema-1.0 registry/compiler, evidence age/delay and
observable recovery; the broader design below remains proposed. No experiment
or model call is authorized by this document.

The subsequent [route checkpoint](ROUTE_COMPLEXITY_ACCEPTANCE.md) implements
a bounded native host-ACL profile with configurable depth/alternatives,
strong-account dead ends and explicit privileged pivot deployment. Sustained
objectives, arbitrary topology and behavioral calibration below remain proposed.

## Research direction

The main comparison remains **hierarchical versus swarm LLM attacker teams**.
The motivation is to study coordination when cyber operations demand reasoning,
evidence integration and adaptation. Single-agent and competent rule-based
policies establish whether the task actually exposes those demands; they do not
replace the organizational research question.

Our target is a behaviorally credible agent-based model: actions change the
environment, defenders react to their own evidence, information becomes stale,
and teams must reassess plans. The graph can remain visually abstract. Neither
a larger graph, extra randomness, nor an LLM choosing actions establishes
realism by itself. Do not require the world to be unsolvable by every possible
rule system; measure the limits of declared, frozen baselines under matched
information and resources.

## Research evidence and consequences

This is a focused primary-source update, not an exhaustive novelty review.

| Source inspected | Evidence relevant here | Design consequence / remaining distinction |
| --- | --- | --- |
| [CAGE Challenge 4 specification](https://github.com/cage-challenge/cage-challenge-4) | Segmented enterprise networks, active defenders, benign users, changing mission/connectivity policies, deception and action durations. | Reuse these as modeling precedents. CC4 is a separate defensive benchmark and engine branch; these features are not automatically available in our pinned adapter. |
| [Towards Production-Worthy Simulation for Autonomous Cyber Operations, 2025](https://arxiv.org/html/2508.19278v1) | Extends CC2 with patch/isolate/unisolate and studies RL in the resulting environment. | Qualification must include intervention effects. Its stochastic patch-score mechanism is a published abstraction, not ground truth about patching; use explicit service/version compatibility in our proposed model. |
| [Context, Reasoning, and Hierarchy, May 2026](https://arxiv.org/html/2605.16205v1) | Controlled CybORG defensive study of context, deliberation and hierarchy with token accounting; demonstrates that those design choices interact. | Existing nearby work rules out a broad claim of first LLM hierarchy in CybORG. Our candidate distinction is offensive peer-versus-leader coordination across controlled adaptation/complexity conditions. That distinction still needs a fuller review and results. |
| [Towards a Science of Scaling Agent Systems, v3](https://arxiv.org/html/2512.08296v3) | Architecture effects depend on task structure and resource overhead. | Independently manipulate sequential dependency and parallel opportunities; keep world/action/model budgets matched. Its other-domain findings are not cyber results. |
| [HPTSA](https://arxiv.org/html/2406.01637v1) | Prior hierarchical offensive LLM agents. | Organization comparison needs a specific tested mechanism, not merely an LLM attacker implementation. |
| [Cybench](https://arxiv.org/abs/2408.08926), [AutoPenBench](https://arxiv.org/abs/2410.03225) | Cyber-agent evaluations include executable security tasks of varied difficulty. | Optional isolated-system validation can complement simulation. Neither benchmark alone supplies our dynamic organizational experiment. |
| [MITRE network service discovery](https://attack.mitre.org/techniques/T1046/) and [remote services](https://attack.mitre.org/techniques/T1021/) | Document real discovery and remote-access behaviors. | Use technique descriptions to justify modeled behaviors. A technique mapping does not validate an exploit probability or a simulator. |
| [ODD model-description protocol](https://www.ufz.de/index.php?en=40429) | Standardized description of agent-based model structure. | Document entities, state, observations, processes, scheduling and submodels alongside tests and behavioral validation. |

## What the installed system actually supplies

Audited local files: `packages/engine_worker/runtime.py`,
`packages/engine_worker/scenario.py`, and the pinned CybORG action implementations.

| Mechanism | Current behavior | Needed for this research |
| --- | --- | --- |
| World | Scenario2 with 13 hosts and three routers; workers start on User0. | Materialized variable layouts and services; alternative routes and objectives; optional different footholds matched across organizations. |
| Decisions | Five actions: Sleep, discover systems, scan services, abstract exploit, escalation. | Strategic target/controller/path selection first. If studying vulnerability selection, add an explicit catalog of existing native techniques and qualify it; currently the engine selects the concrete exploit. |
| Defense | Sleep or Monitor, with Green asleep. | A bounded observation-driven defender; separately qualified removal, restoration, isolation and patching. Monitor does not repair anything. |
| Access policy | Legacy hostname-specific Operational gate; physical routes. | Generic actor/session/source/service reachability. The inherited gate can accept inactive Enterprise sessions; do not use it in recovery profiles. |
| Knowledge | Own observations, native cache, verified peer addresses, provenance. | Observation timestamps, contradiction handling, stale beliefs and legal re-observation; no silent truth refresh. |
| Time | One joint tick with recorded native ordering. | Explicit defender reaction latency first; multi-tick action durations only after busy/ordering semantics are qualified. |
| Communication | Directed links, delay, loss, capacity, TTL and outages. | Reuse existing overlay; do not interpret these values as physical cyber-network bandwidth. |

Native `Remove` depends on a defender's suspicious-PID knowledge and its own
host session. `RestoreFromBackup` alters host state and session registries.
Their presence in source does not establish correct effects on our named
multi-attacker team. Test before enabling. Patch/isolate/re-entry/credentials
are not currently supported researcher controls.

## Complexity is a vector of separately configurable mechanisms

The following modules are our proposed design choices. Each has `enabled`,
version, validated parameter ranges, explicit dependencies and acceptance
fixtures. Presets are named bundles of resolved values; no invisible global
"difficulty" multiplier changes transition rules.

| Module | Add and adjustable controls | Why it matters | Qualification |
| --- | --- | --- | --- |
| Topology and dependencies | Hosts/zones, alternative paths, dependency depth, branch width, bounded dead ends, gateway policies. | Distinguishes sequential planning from parallel exploration and route reassignment. | Every intended route has native access prerequisites; blocked shortcuts fail; labels alone never confer access. |
| Service/privilege diversity | Versioned service templates, exploit compatibility, user-versus-privileged outcomes, escalation prerequisites, optional explicit native technique selection. | Scanning every host followed by the same exploit loop should not encode the entire solution. Different evidence should justify different actions. | Test vulnerable and patched variants, own-cache requirements, controller types and each supported technique. Never reveal a guaranteed-success candidate list. |
| Observation and beliefs | Limited discovery scope, worker-local evidence, scan timestamps, bounded observation delay; optional decoys/noise. | Teams must request and reconcile evidence, distinguish an old report from current access, and spend actions on verification. | No hidden inventory/policy/patch flag enters prompts or candidates. Hidden-state changes are observationally indistinguishable until a legal signal arrives. |
| Defender | Passive, observation-driven fixed policy, separately labeled open-loop schedule; sensor coverage, detection parameters, reaction delay, action budget and cooldown. | Attacker choices influence risk and future access. Recovery/replanning becomes part of the mission. | Defender receives only its telemetry; no omniscient compromised-host query. Alerts, decisions and physical effects are separate logged events. |
| Technical change | Qualified isolation/unisolation, service patch/maintenance and host restoration. | Old service scans/routes/sessions can stop being usable; alternative routes can become valuable. | Atomic native state/cache/session updates; surviving reachable solution or an explicit infeasible outcome. Changes do not target an architecture label. |
| Mission | Target count, priorities, dependency graph, deadlines, stable-access dwell time; later business-service objectives. | Workers must allocate effort and coordinate evidence, while success requires actual access. | Scorer checks engine state. A report or completed task label never satisfies a physical prerequisite. Target identity/mission updates are public and identical across treatments. |
| Time and resources | Horizon, per-team/per-worker action capacity, verification cost; later action durations and detection-risk profiles. | Allows competing plans and urgency without handing teams extra effort for free. | One world clock, declared ordering, defender advances once; busy actors cannot take another action. Token time does not secretly advance simulation. |
| Communication | Existing topology, delay/loss/capacity, claim TTL and link interruptions. | Produces stale assignments, incomplete leader information and peer disagreement. | Delivery-only knowledge changes; provenance and copy accounting; physical isolation does not imply message interruption unless an explicitly selected coupling module specifies it. |
| Benign activity — later | User demand, service availability, maintenance and alert noise with separate seeds. | Supports realistic operational tradeoffs and interpretation of defender alerts. | No automatic new red footholds or successful attacks. Phishing/spawn behavior requires its own explicit, qualified initial-access model. |

Increasing node count is a scale treatment, not automatically a reasoning
treatment. Longer observation delay is distinct from transport delay. Genuine
stochastic uncertainty is distinct from withholding all useful evidence.

### Recommended first substantive profile

Build `enterprise_research/branching_recovery` after qualifying its static
components. Proposed development instance: four zones, 16 ordinary hosts plus
separately counted routers, two sensitive targets, two alternative technical
routes and heterogeneous services. Counts are starting design values, not
empirically calibrated difficulty.

1. Workers start with the same legitimate local foothold information. Optional
   dispersed starting access is a later matched sensitivity, not a benefit
   silently given to swarm.
2. Native discovery produces different usable leads as workers explore branches.
   One branch leads through an observed bridge service; another offers a longer
   alternative. A bounded dead end is diagnosable by a scan.
3. A scan produces actual service evidence. Agents choose which target/controller
   to use, whether to refresh an old scan, or which qualified technique to try.
   No native exploit effect is fabricated by the LLM or UI.
4. A defender observes an alert from its own sensor history, investigates and,
   after a declared delay, removes access or isolates the implicated host. An
   open-loop version uses a fixed schedule to isolate change from reactivity.
   For the first recoverable profile, response scope excludes the initial-entry
   host, a declared simplifying assumption; it can remove downstream footholds.
   Later full-entry-loss profiles require separately qualified re-entry or
   explicitly score permanent loss as failure, with no automatic new foothold.
5. The affected worker learns about lost access or failed connectivity through
   permitted results/status. Other workers only learn through delivered reports
   or their own observations. A failure does not magically reveal "patched".
6. The team must refresh evidence, revise claims/assignments, change controller or
   route and reallocate effort toward both targets.
7. A mission variant requires qualifying access on both targets for a declared
   number of consecutive ticks. Defense continues during this interval; the
   existing immediate-success scorer must therefore be replaced for this profile.

Hierarchy and swarm face the same instance, action opportunities and defense
policy. Their information-flow/assignment mechanisms differ. This episode
permits observable organizational mechanisms without asserting a winner.

### Complexity ladder and independent sweeps

| Preset | Enabled changes relative to earlier level | Scientific purpose |
| --- | --- | --- |
| C0 — static control | Qualified linear profile; no active defense, no uncertainty overlay; healthy transport. | Establish engine correctness and where a simple policy suffices. Keep legacy as a separate integration fixture. |
| C1 — branching | Alternative routes, two objectives, service/privilege diversity. | Isolate decomposition, information gathering and duplicate work. |
| C2 — changing access | C1 plus one bounded restoration/isolation event and stale observations. | Measure evidence refresh, reassignment and recovery. Start open-loop, then reactive. |
| C3 — coordination pressure | C2 plus bounded reactive defense, dwell/deadline constraints and one selected communication impairment. | Measure organization under combined time and information pressure. |
| C4 — operational extension | C3 plus qualified decoys/benign activity and action durations. | Broader behavioral validity; optional expansion after the core study. |

Use the ladder for exploration; use factor-controlled comparisons for inference.
For example, keep topology and mission fixed and sweep defender delay, then
toggle only stale reports, then vary transport. Do not attribute C0-versus-C3
differences to any one component. Increasing complexity is not guaranteed to
increase measured difficulty monotonically.

## Module boundaries and repository layout

Extend the current adapter; preserve the working legacy profile. Split its
responsibilities incrementally rather than replacing the entire engine.

```text
packages/contracts/
  research_profile.py          # proposed schema-2.0; strict discriminated modules
packages/engine_worker/
  research/
    registry.py                # capabilities, dependencies, qualified combinations
    compiler.py                # config + generation seeds -> materialized manifest
    topology.py                # native hosts, links, access-policy construction
    service_templates.py       # versioned native-compatible service/privilege data
    reachability.py            # shared technical route/source/service rules
    transitions.py             # bounded native state mutations; no cognition
    defender.py                # policy on defender observations only
    sensors.py                 # native events -> recipient-specific observations
    temporal.py                # world-clock events, durations and phase ordering
    missions.py                # state-based objective/dwell evaluation
backend/app/
  beliefs.py                   # timestamps, conflicts, observations versus reports
  baselines.py                 # versioned local rules/planners; same public view
  scenario_capabilities.py     # exposes qualified knobs, no unrestricted plugins
  evaluation.py                # new event reducers; keep historical metric versions
scenarios/research/
  templates/ presets/ splits/  # declarative recipes and immutable split manifests
frontend/src/
  ComplexityEditor.tsx         # capability-derived module controls and presets
  EnvironmentEvents.tsx       # researcher events versus worker-visible signals
tests/research/                # module, composition, privacy, lifecycle fixtures
docs/research/
  BEHAVIORAL_VALIDATION.md     # future ODD/rationale/evidence dossier
```

Names above are proposed target files. Do not imply they currently exist.
Only `engine_worker` imports CybORG or reads privileged state. Belief updates,
baselines and LLM policies use the same agent-visible channel. Existing policies
and communication bus retain their organization responsibilities.

### Required module contracts

- `describe()` returns module ID/version, parameter schema, ranges, required
  actions/modules, supported combinations and qualification status.
- `validate(resolved_profile)` checks dependencies and combinations before any
  child process starts. Enabled unknown/unqualified modules are rejected.
- `materialize(recipe, seed_namespace)` produces immutable native world inputs
  and scheduled exogenous events. Compiler output is separate from policy input.
- `apply_transition(command, native_state, context)` is engine-only, atomic and
  returns actual before/after deltas. Commands come from qualified actions or
  environment-event specifications; never from arbitrary JSON callbacks.
- `project_observation(event, recipient, previous_belief)` discloses only legally
  sensed facts with source and timestamp. It cannot return hidden cause labels.
- `evaluate(native_state, mission_history)` computes objective/progress for the
  researcher and scorer; no truth feedback goes to policies by default.

Register concrete module IDs in code. Config contains data only; no import
paths, dynamic Python expressions or user-supplied transition code. Dependencies
are checked as a graph, and hook order is fixed, not registry iteration order.

Each field receives a published numeric range only after native/template
qualification. Semantic checks additionally constrain branch/dependency counts
to available hosts, target roles to generated non-entry assets, service choices
to supported OS/session combinations, and response targets to their declared
scope. A requested layout must be realizable; do not silently clip values.

### Clock, ownership and causal ordering

At boundary t, deliver messages and authorized observations; update private
beliefs; collect proposals from that information; admit actions under the common
schedule; execute one native joint tick; apply due qualified environment events
in their declared phase; project observations; evaluate the mission; persist.
Pin exact native priorities and all event tie-breaking. Multi-tick durations
must align with this clock without calling the native tick once per worker.

A reactive defender chooses from observations available at its decision boundary.
It cannot react to an attacker action that has not executed. Log signal time,
decision time and effect time. An event caused by a particular action remains
distinct from a scheduled exogenous maintenance event.

Do not only block the proposed high-level action in a gateway while leaving its
native concrete action able to bypass generic policy. Both route validation and
native execution must use the same reachability predicate, including source
host, active owned session, destination/service and current policy revision.
Remove the inherited hostname special case only in the new profile adapter or
a documented, tested fork patch. Do not disable it globally for legacy episodes.

Cache invalidation is explicit: service/version changes invalidate affected
native eligibility caches; session loss invalidates controller use; belief
history remains marked old. Do not update an attacker’s knowledge with a hidden
patch event just because the engine knows it happened.

## Proposed configuration and compatibility

See [the design-only JSON example](examples/complexity-profile.v2.design.json).
It illustrates the profile recipe, modules and split metadata. It is **not** an
executable `EpisodeConfig`; current schema-1.0 must reject it. Phase 3 introduces
an explicit versioned contract and an adapter for legacy configs; do not add
silent defaults that change historical worlds.

Compiler output stores all resolved settings, host/service templates, policy and
sensor versions, scheduled event selectors/times, mission, separate seed
namespaces, and hashes. World generation does not consult organization or model.
Attach treatment config separately. A reactive defense uses the same policy and
seed in paired worlds but may produce different events because attackers act
differently; do not force identical effects and call it reactive.

Preset changes expand visibly to module values. Manual editing of one value
marks the preset custom. Advanced JSON and CLI use exactly the same validation.
Turning a module off does not leave hidden mutations or metrics from a prior run;
every world gets fresh module state. Scenario changes apply only to new runs.

## Researcher controls and visualization

| Researcher can configure without code | Visible evidence | Programmer must implement/qualify |
| --- | --- | --- |
| Existing preset; hosts/zones/routes within limits | Actual graph, zone/service inventory in truth view, private discovered graph. | Generator constraints and generic reachability. |
| Defender preset, sensor coverage, reaction delay and response budget | Defender alerts, decisions and effects in researcher timeline; permitted symptom in private view. | New sensor or defense transition. |
| Observation delay, decoy density when qualified | Evidence source/age, reported belief, contradiction/unconfirmed status. | Observation semantics and uncertainty model. |
| Target set, dependency/dwell/deadline preset | Objective graph, engine-confirmed access, dwell counter/reset and missed deadlines. | New physical mission primitive. |
| Module toggles and transport settings | Current link states, queued/dropped reports, claims/assignments and reassignment history. | A new module or unqualified combination. |
| Comparison matrix and immutable preset export | Factor values, matching world ID, split, counts and exclusions. | Batch execution and new metric reducer. |

The researcher truth timeline may explain "defender patched service"; the worker
view must show only its permitted failed attempt, rescan or notice. UI animation
never creates state transitions. In evaluation mode, toggles cannot mutate an
active world; exploration interventions retain the existing invalid-for-study
flag. Paused initialization must remain available for every qualified preset.

## What counts as behaviorally realistic enough

Maintain a claim/evidence register for each mechanism: intended real process,
state/action/observation mapping, simplifying assumptions, source, software
fixtures, expert or isolated-system comparison, sensitivity range and evidence
level. Use labels `specified`, `software-qualified`, `expert-reviewed`, and
`range-compared`; passing pytest does not imply empirical validation.

Required patterns for the first research family:

1. A patched incompatible service prevents the affected exploit; repeated retries
   alone do not undo a patch. Alternative legitimate paths remain possible when
   the profile declares a recoverable mission.
2. Isolation prevents relevant remote access without automatically destroying
   every persistent session; restoring a host can remove access and reset
   services according to a documented model. Test each operation separately.
3. Discovery/attack traffic can generate defender evidence; delayed, budgeted
   responses follow that evidence rather than true compromise labels.
4. Information learned earlier can become wrong; fresh observation can detect
   some changes. A stale peer report never recreates lost native access.
5. More simultaneous objectives increase task-allocation opportunities; tightly
   coupled dependencies require sequencing. Those are measurable properties of
   the generated mission, not labels in a preset name.

First verify these transitions and privacy invariants. Then obtain expert review
of representative trajectories and parameter assumptions; where stronger transfer
claims are intended, compare selected transitions/organizational patterns in a
small isolated lab. [CALDERA](https://github.com/apache/caldera) is a possible
adversary-emulation tool for that later check, not a replacement engine or an
already configured dependency. Report disagreements and scope limits.

Do not describe heuristic probabilities as measured incident rates. Start with
deterministic bounded change for causal diagnosis, then sweep documented
uncertainty ranges. Packet fidelity, real exploit execution and human attacker
equivalence remain outside the simulated result unless separately established.

## Qualification and calibration gates

Before enabling a module: valid configuration, positive/negative native effects,
ownership/privacy, disable/no-op parity, fresh-world reset, event/replay integrity,
and composition fixtures with its required modules must pass. A disabled module
does not consume unrelated RNG streams. Preserve a pinned legacy replay/mission
fixture as regression evidence.

Before a research pilot: qualify at least C0, C1 and C2; inspect actual decisions,
changed routes, legitimate lost access, observable recovery and distinct
coordination traces. Avoid a core suite in which every method succeeds instantly
or every method fails because all entry access is permanently removed.

Difficulty calibration uses **development worlds only**, with a transparent
scripted policy, a local-information planner that can refresh/replan, one LLM
worker, independent LLM workers, hierarchy and swarm. No baseline gets hidden
world inventory; no architecture-specific helper solves allocation behind the
scenes. State tracking/allowed-value filtering is shared infrastructure, not a
secret planner. The old fixed retry limit must not become a deliberately weak
comparator under maintenance events.

Freeze profile/module versions, budgets and evaluation split before final runs.
Hold out service/path combinations, intervention timing and some sizes, not
merely IP addresses. Stratify by task dependency, branching and defender pressure;
use paired world comparisons and targeted module ablations. Do not choose
complexity cells because a preferred method wins in the held-out test.

Additional metrics: evidence age at decision, refresh actions, actions based on
invalidated evidence, time from observable disruption to renewed valid progress,
assignment/claim revision, blocked-route retries, access loss/recovery, target
dwell and defender reaction. Use observable disruption time for the primary
adaptation metric; hidden change time is a separately labeled researcher metric.
Declared rationale is not proof of causal reasoning; use trajectories and
ablations to assess a mechanism.

No numeric difficulty threshold or paper result is established at design time.
Pilot sample counts/costs must include the chosen baselines and complexity cells;
the earlier 36-episode organization-only illustration is not a sufficient final
design by itself. All research/model execution still requires explicit scope.

## Build order

**Backend decision updated after inspection:** [the CC4 audit](CC4_COMPATIBILITY_AUDIT.md)
supports a separate CC4 adapter as the target for the complex research profiles.
First qualify the production research generator, adapter contracts, reset,
private observations, durations, missions and replay. Existing legacy work is
retained. Native restore/block/allow and action durations can replace proposed
legacy extensions where their composed semantics are qualified. The audit does
not implement this migration or change the proposed profile schema.

1. **T12a–T12b:** strict profile registry/compiler and generic static native
   topology/service/reachability. Preserve legacy.
2. **T12c + T13a:** timestamped private beliefs and bounded observable recovery;
   open-loop fixtures first, then defender driven by its own observations.
3. **T12d:** physical multi-target/dwell mission and legal recovery opportunities.
4. **T12e:** capability-based UI presets, event/belief visualization and exports.
5. **T12f + T11:** strong comparison policies and live-model qualification on
   approved development tasks. T11 accounting work can proceed independently;
   it does not establish environment validity.
6. **T13b:** optional technique-choice, deception, duration and benign-activity
   extensions after their native semantics pass.
7. **T14–T17:** adaptation metrics, controlled sweeps, calibration/validation,
   freeze and final evaluation. Do not run a hypothesis study before this gate.
