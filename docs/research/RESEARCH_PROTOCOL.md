# Research protocol and evaluation design

**5 October 2026 revision:** the [bounded graduation plan](REVISED_GRADUATION_PLAN.md)
sections 2 and 12–14 now govern questions, core families, controls, fairness,
qualification, held-out worlds and evaluation. Hierarchy versus swarm remains
primary. A few evidence/capability/change mechanisms replace the broad complexity
ladder as required scope. Two/four workers and one primary model are required;
second-model robustness, broad ablations and range transfer are extensions.
Historical proposal detail below is retained but conflicting requirements are
superseded. No evaluation was run; all scientific claims remain hypotheses.
[Primary-source update and coverage](PLAN_SOURCE_AUDIT.md).

## 1. Research objective

Study how hierarchical and swarm organizations of LLM-driven attacker teams
coordinate and adapt in complex, partially observed, changing enterprise tasks.
Use CybORG's host/service/session/action model as the technical environment;
explicitly model uncertainty, changes, communication, and coordination.

Working framing: **Coordination and Adaptation of LLM Cyber Teams in Changing
Environments**. This is a research direction, not a novelty claim or finalized
title. **Hierarchy versus swarm remains the primary comparison.** LLM reasoning
is motivated by the intended adaptation demands; fixed-rule, replanning/search,
single-LLM and independent-worker baselines diagnose whether those demands and
organizational benefits are present under matched information and resources.

The directional hypothesis is that LLM policies will adapt and generalize better than fixed policies when they must combine incomplete evidence, recover from changed conditions, and solve held-out multi-step tasks; this may cost more. A simple known route may be solved more cheaply by a scripted or graph-search policy, so include such a condition as a sanity check. Do not tune tasks to guarantee an LLM win: whether the predicted advantage appears, where it appears, and its cost are the empirical result. If the goal is to claim human-like performance, a human comparison is needed; otherwise do not equate LLMs with human attackers.

## 2. Positioning against literature

| Prior work | Relevant overlap | What this study must distinguish |
| --- | --- | --- |
| [HPTSA](https://arxiv.org/abs/2406.01637) | Hierarchical LLM teams for offensive tasks. | A controlled organizational study of sequential network operations, private observations, transport conditions, and cost; not the first cyber LLM team. |
| [Liu, multi-agent incident response](https://arxiv.org/abs/2412.00652) | Centralized, decentralized, and hybrid cyber-team comparisons. | Offensive technical state transitions rather than a tabletop incident-response game; stronger resource controls and scenario diversity. |
| [Agent scaling study, version 3](https://arxiv.org/abs/2512.08296v3) | Architecture effects depend on task properties and budgets. | Cyber-specific access prerequisites, multi-stage missions, and failures under restricted information sharing. |
| [SecurityBot](https://arxiv.org/abs/2403.17674) | LLM/RL integration in CybORG. | Test adaptive reasoning on held-out changing tasks, then study how team organization changes its effectiveness; verify the precise overlap in the literature review. |
| [CC4](https://github.com/cage-challenge/cage-challenge-4) | Enterprise multi-agent defensive benchmark. | A customizable offensive-team protocol, or a separately labeled later transfer study. |
| [Context, Reasoning, and Hierarchy, 2026](https://arxiv.org/html/2605.16205v1) | CybORG defensive LLM hierarchy/context/deliberation study. | Offensive peer-versus-leader coordination with controlled branching, stale information and reactive change; a candidate distinction, not yet a novelty claim. |

Before submission, search current cyber-agent and general multi-agent literature, maintain an evidence table with task/action/observation/coordination/budget/evaluation columns, and verify all citations. References [8], [9], and [14] in the original report contain arXiv identifiers for unrelated papers. Remove unsupported claims that coordinated offensive LLMs are an empty niche, RL agents cannot adapt, or LLM agents are necessarily human-realistic.

Using a familiar engine does not itself constitute novelty. The candidate
contribution is a controlled result explaining organizational differences under
specified cyber adaptation demands and budgets. Compare against transparent
rule/planner policies with the same observations and actions; report simple
tasks where they suffice as well as changing tasks where brittleness is
hypothesized. Adaptive organization is optional and must be tested on held-out
conditions. See [the renewed evidence and design](ENVIRONMENT_COMPLEXITY_DESIGN.md).

## 3. Questions and hypotheses

- **Primary RQ:** At matched worker/action opportunities and LLM resources, how
  do hierarchy and swarm differ in success, recovery, duplication and cost as
  technical dependency, partial knowledge and defender pressure vary?
- **RQ2:** Which coordination mechanisms explain those differences: information
  freshness, task allocation, conflict resolution or replanning after access loss?
- **RQ3:** Do the chosen complexity conditions reveal benefits beyond a
  competent rule/replanning policy, a single LLM and independent LLM workers?
- **RQ4:** Do architecture effects generalize to held-out service/path/change
  combinations, and how do transport delay/loss and model family modify them?
- **Optional RQ5:** Can a pre-specified adaptive organization improve the success/cost tradeoff on held-out conditions using only agent-visible signals?

Pre-specify architecture-by-complexity and architecture-by-communication contrasts
alongside diagnostic cognition comparisons. Declare conditions where rules
should suffice and where adaptation is expected to matter. A tie or baseline
win remains evidence; final test worlds never become a benchmark-tuning set.

## 4. Scenario suite

The engine supplies transitions; the research layer supplies reproducible worlds and missions. Build scenario profiles by reusing audited host templates/services/actions, not by inventing a second complete cyber simulator. Initial default environment is a four-zone enterprise research family: entry/DMZ, user, enterprise, and sensitive assets. Define every allowed path and access prerequisite in the materialized world.

| Profile | Purpose | Required properties and qualification |
| --- | --- | --- |
| `enterprise_legacy` | Integration baseline. | Existing Scenario2 asset/action model, three subnets, fixed legacy operational gate. Keep its labels/logic unchanged; explicit attacker overrides and team score. Never describe this as the final four-zone scenario. |
| `enterprise_research/linear` | Control condition for familiar, sequential work. | Four zones with a qualified chain of discover/service-scan/access/escalation steps; at least one designated sensitive target. This should expose tasks a known-path planner can solve efficiently, not be presented as evidence for LLM superiority. |
| `enterprise_research/branching` | Evidence integration and task decomposition. | Several reachable paths/targets, dead ends, and controlled initial knowledge. Workers receive different legitimate observations; success requires privileged sessions on all designated targets, not one lucky foothold. |
| `enterprise_research/recovery` | Adaptation/generalization condition. | Qualify a defender that changes access or removes/restores sessions after agents begin. Include held-out timing/target combinations, preserve observable evidence, and log interventions identically across modes. |
| Communication overlay conditions | Coordination stress without changing technical world. | Healthy, bounded delay/loss, sparse links, and a pre-specified leader-link interruption. Interruptions are task conditions, not proof that all swarms are robust. |

Every profile declares supported worker counts, compatible session/action types, world parameters, privilege goal, permitted transport knobs, defender behavior, termination rules, and validated engine revision.

Generation constraints:

1. Fix/materialize hosts, services, patches, users, privilege opportunities, links, footholds, and target IDs before a run.
2. Verify target solvability with a scripted reference policy for the no-defender baseline and verify negative access cases. Separately implement transparent fixed-policy baselines for comparison; do not let either the reference solver or any competitor read hidden paths or privileged truth.
3. Vary actual layouts, services, entry knowledge, and dependencies across instances; changing only IP addresses is insufficient diversity.
4. Use familiar labels for the legacy gate only. Generic research profiles disable that legacy special case and use the explicit tested research reachability policy.
5. Preserve source transition assumptions; if adding probability, vulnerability choice, service changes, or routing behavior, version and validate it as a new simulator profile.

Four-zone topology alone does not produce believable segmentation. Reachability fixtures must check source/session ownership, designated bridge-access prerequisites, observation restrictions, and failures for blocked paths. Do not assume arbitrary NACL port rules are enforced by the audited modern action path.

Dynamic host removal and native arbitrary checkpoint restoration are deferred. Use qualified session removal/service restore actions and coordination-link changes first. Random scenario instances generated for development are separate from held-out evaluation instances.

### 4.1 Revised complexity requirements

Implement independently versioned topology/dependency, service/privilege,
observation/belief, defender, technical-change, mission and temporal modules;
reuse the communication overlay. Benign activity/deception/durations are later
qualified extensions. A preset expands to explicit values and supported
combinations; it is not a hidden difficulty multiplier. The
[module design](ENVIRONMENT_COMPLEXITY_DESIGN.md) specifies contracts, UI/code
boundaries, a branching-recovery episode and proposed C0–C4 ladder.

The first substantive suite requires branching legal routes, heterogeneous
service/access prerequisites, time-stamped private evidence, bounded restoration
or isolation, and multi-target objectives with optional access dwell. Use
open-loop change to isolate recovery, then an observation-driven defender with
specified sensors, latency, budgets and cooldown. A reactive defender cannot
read a global compromise inventory. Equal defender policy does not imply equal
events when attacker behavior differs.

Model scale, reasoning demands and stochastic noise separately. A larger graph
or lower success probability alone is insufficient. Keep alternative recovery
opportunities; identify infeasible worlds rather than giving an agent an
automatic foothold. Rule-based and single-agent performance diagnose saturation
and limits; no winner is an environment-validity criterion.

## 5. Experimental conditions and baselines

Diagnostic cognition/control conditions supporting the organization question:

- LLM policy/worker on the changing and held-out task conditions, with bounded memory, actions, time, and model budget.
- A fixed scripted policy and a transparent planner/search baseline using the same agent-visible information and action opportunities. Tune their rules on development tasks only; freeze before held-out evaluation. Do not intentionally cripple them, and do not expect them to solve genuinely novel combinations without evidence.
- A familiar static/linear condition where graph search or known rules may match or beat an LLM, establishing when language-model reasoning is unnecessary.

Primary organizational conditions among LLM-controlled teams:

- Hierarchy: N workers plus a coordinator; star communication; reports/assignments only through modeled transport.
- Swarm: N peer workers; independent local memory; declared peer graph and claim protocol.
- Single LLM worker: whether coordination is useful compared with a simpler actor.
- Independent LLM workers with no communication: separates interaction benefits from having several actors.

Optional additions: fixed hybrid, adaptive topology, RL baseline if a genuinely compatible trained agent is available and its training budget is documented. Do not relabel an old defender as an offensive RL baseline or report a random policy as a strong comparator.

Match within every cognition or organization comparison:

Rule/planner policies use the same structured facts, legal actions and world
clock as LLM policies. Do not force them to parse prose while an LLM receives
extra facts, nor supply a hidden route plan to either. Give replanning baselines
documented verification/retry rules; the software fixture's fixed retry limit
is not automatically a scientifically adequate dynamic-environment baseline.

| Controlled factor | Rule |
| --- | --- |
| World | Same materialized instance and target objective. |
| Attacker resources | Same N workers, initial host access/privileges, action catalog, and session rules. |
| Model | Same worker/coordinator model family and generation settings in the primary comparison. Heterogeneous teams are a separate factor. |
| Cognition | Same context cap, memory encoding, and common action descriptions; role instructions differ by architecture and are versioned. |
| Total LLM tokens | Count all leader, worker, summarization, repair, and retry usage; enforce a common ceiling. |
| Cyber actions | Same scheduler and action opportunities; log attempted/rejected/executed counts. |
| Communication | Same transport delay/loss and total byte/envelope capacity; graph structure differs as the treatment. |
| Defender | Same fixed policy/version and initial conditions; separately report open-loop scheduled and reactive defenses. |
| Termination | Same objective, horizon, and budget stop rules. |

More workers add native sessions and action capacity under `per_worker`. Do not attribute a faster mission solely to intelligence. Repeat selected conditions under `team_cap=1`, equal total budget, and matched initial-access sensitivity. Hierarchy's extra coordinator is included in cost and counts; show a matched-total-reasoner analysis separately.

Use distinct RNG namespaces for world generation, native simulation, message loss, and neutral scheduling. Provider seeds, if supported, are recorded but do not guarantee identical responses. Native stochastic draws may diverge when actions differ, even with the same native seed; matched initial worlds are not identical counterfactual random outcomes.

## 6. Metrics with precise definitions

Mission success is evaluated from privileged engine state after execution, never from model text or a dashboard label. Primary mission success means an active qualifying privileged session from any registered red-team actor exists on every designated target at the end of a tick. Linux `root` and Windows `SYSTEM` are the initially supported privilege labels; other privilege equivalences require a catalog extension. Exclude already-owned entry hosts from the mission target count.

| Metric | Definition and reporting |
| --- | --- |
| Success | Binary objective attainment before a stop limit; primary rate includes all valid completed attempts. |
| Completion ticks | First tick achieving objective. Unsuccessful runs are censored/limited outcomes; do not pretend they finished at the horizon. |
| Action effort | Requested, executed, rejected, and successful cyber-action counts, categorized by action. |
| LLM usage | Actual provider input/output/cached/reasoning-token fields when available, raw accounting preserved; do not double count overlapping fields. Record unknown fields as unavailable. |
| Monetary cost | Usage priced under a versioned rate table; missing price fields remain missing. Local inference uses measured time/resource estimates separately. |
| Token efficiency | Success probability as a function of total budget; also tokens spent across all attempts per successful mission. Report undefined values if there are no successes. |
| Coordination cost | Call/token/time shares for coordinator, workers, summaries, repair, and communication generation; bytes/delivery events separately. |
| Duplicate work | Repeated actor/action-family/target operations within a defined window without a newer corroborated state change that justifies repetition. Publish window and exclusion rules. |
| Invalid decision rate | Structurally malformed or evidence/permission-invalid proposals divided by total proposals; distinguish native technical failures. |
| Communication behavior | Enqueued/delivered/dropped/expired copies, UTF-8 bytes, delivery delay, known claim conflicts. |
| Resilience | Change in success/effort under interruption and ticks to recover useful progress; progress criterion defined per mission. |
| Strategy variation | Action-sequence edit distance and target-selection diversity within matched worlds, plus objective variance. Lower diversity is not automatically better. |
| Operational impact | Qualified service availability/impacted-target state; secondary to privileged-access mission unless a disruption profile is explicitly selected. |
| Native reward | Optional engine/team calculator output; contextual diagnostic, not a universal cross-scenario performance score. |

Implement a team score that counts each qualifying host once across all red actors. Score a team once per tick; `parallel_step` returns repeated team reward values per actor. Register custom calculators directly in the programmatically constructed scenario rather than using an unsupported string in the stock factory.

Native reward and the objective evaluator remain separate: a policy should not accidentally receive hidden progress from privileged metrics. Initially policies receive ordinary action results and the public mission description, not a true-state score. Any reward feedback treatment is explicit and matched.

## 7. Sample plan and costs

Run stages instead of launching a large factorial sweep immediately:

1. **Engine qualification:** scripted/mock policies only; all scenario/action/ownership/information tests pass. No paid API access required.
2. **Pilot:** one model, hierarchy/swarm, three scenario families, healthy/degraded transport, three world seeds, one repeat: `2 x 3 x 2 x 3 = 36` episodes. Diagnose saturation, trivial targets, deadlocks, invalid actions, and API costs.
3. **Core evaluation:** choose qualified conditions and a predeclared practically meaningful difference. Estimate required distinct-world count from pilot variance and power/precision analysis. Fifty worlds with two provider repeats is a provisional planning number, not proof of statistical significance.
4. **Generalization:** repeat the core comparison on a second model family; run selected team-size and action-cap sensitivities; run baselines; test held-out network sizes and transport conditions.
5. **Optional adaptive method:** tune on development worlds, freeze parameters, then compare on the untouched held-out suite.

The 36-episode illustration covers only organization conditions. A revised
pilot must resolve the selected module cells and diagnostic baselines, display
their full episode count and obtain explicit execution scope. Use development
worlds to identify saturation and impossible recovery; module qualification
alone is not a calibrated difficulty result.

For illustration, the hierarchy/swarm comparison with 3 scenario families, 2 transport settings, 2 model families, 50 worlds, and 2 repeats requires `2 x 3 x 2 x 2 x 50 x 2 = 2,400` episodes before additional baselines. The UI must display this count and a pilot-based estimate. No fixed money/time estimate is justified before actual usage and local speed are measured.

Batch stop limits include total provider cost, total tokens, and maximum technical failure rate. Pause scheduling new episodes when a limit is reached; do not truncate data silently. Provider calls in flight can still incur costs; include them and bound reservations before launching more calls.

## 8. Analysis and reproducibility

Use the world instance as the principal matching/clustering unit. Repeats on one world measure model stochasticity; they are not equivalent to additional independent worlds.

- Aggregate each architecture's repeat outcomes within world, then report paired differences with a bootstrap clustered by world within scenario/model condition.
- Report success-rate confidence intervals and effect sizes. For one repeat per world, a paired binary test can be used; do not apply independent t-tests indiscriminately to success labels or nested observations.
- Report conditional completion effort together with success, and use an appropriate censored-time/restricted-time analysis for failed missions. Failure penalties, if used, are predeclared, not invented after seeing results.
- Analyze architecture-by-task and architecture-by-transport interaction, optionally with a hierarchical/mixed model when sample sizes support it.
- Designate one primary endpoint and a small set of planned contrasts. Correct exploratory multiple comparisons or clearly label them exploratory.
- Publish sample counts, technical errors, refusals, budget stops, manual interventions, exclusions, and sensitivity to exclusion rules.

Distinguish outcomes: succeeded, failed by horizon, failed by budget, provider refusal, provider unavailable, invalid-decision exhaustion, engine error, manually stopped, manually intervened. Refusals and invalid decisions are operational outcomes unless excluded in advance for a justified research question; also report them separately. Engine/transport infrastructure failures are technical failures, retained in logs and retried under a new attempt ID. Never retry ordinary mission failures until success and count only the success.

Provider failures may be retried under bounded transport retry rules; preserve every request ID and usage record. Resuming a batch means skipping verified completed jobs and scheduling untouched/retry jobs, not restoring a partially executed native engine. An interrupted episode restarts as a new attempt from its materialized world; an old attempt remains recorded.

Publish full resolved configs, materialized worlds, code/engine/patch hashes, model identities and parameters, prompt versions, event reducers, raw observations/actions/messages, usage records, and plotting scripts. Browser replay uses recorded snapshots; deterministic decision replay uses saved provider outputs; a fresh hosted-model run is a distinct replication and may differ.

## 9. Ablations and validity checks

Mandatory small ablations: no sharing; no claim mechanism; reduced/delayed reporting; equal team tool capacity; and a no-leader/fixed-dispatch hierarchy baseline where feasible. For an adaptive policy add fixed hybrid, random switching, and a component-removed switch rule.

Information validation: changing an unobserved host/service must not change any agent prompt or action candidate set before disclosure. Leader prompts must depend on received reports, not workers' undisclosed memory. False action-space keys must never appear in prompts. A received report cannot grant a session or native privilege.

Scenario validation: scripted legal paths succeed, impossible/blocked paths fail without engine crashes, alternative service paths are tested, and restore/removal actually changes the scored state. Claim protocol tests must cover delayed claims and genuine duplicate execution rather than a global deduplication shortcut.

Calibration and scope: inspect action simplifications such as fixed exploit selectors, success/detection assumptions, and abstract firewall gates. Perform sensitivity studies over qualified parameters. To claim human attacker behavior, collect a human comparison; otherwise frame results as properties of autonomous LLM teams in this simulator. For stronger real-system transfer claims, validate selected organizational findings in an isolated cyber range; production-network tests are unnecessary for this simulation study.

For every complexity module, maintain a behavioral evidence register containing
the intended real process, simplifying assumptions, primary source, software
qualification, expert review and any isolated-system comparison. Describe the
ABM entities, state, observation and scheduling rules explicitly. Use separate
labels for implementation correctness and behavioral validity. Targeted
ablations disable one mechanism at a time; combined ladder levels are
exploratory bundles. Calibrate only on development worlds and freeze prior to
held-out evaluation. Extend metrics with evidence age/refresh, observable
disruption-to-progress latency, assignment revision, access recovery and dwell.

## 10. Publication decision gates

The workbench is an enabling artifact. It becomes a research paper only after the evaluation yields a defensible new result or validates a method against meaningful baselines.

- Gate A: two genuinely different coordination mechanisms and tested information boundaries.
- Gate B: nontrivial qualified scenarios; hypotheses can be falsified.
- Gate C: fairness under budgets, action capacity, and initial access; independent metric verification.
- Gate D: robust results across held-out worlds, a second model, and relevant stress conditions, with uncertainty.
- Gate E: verified literature positioning and artifacts another researcher can rerun.
- Optional security-venue gate: additional evidence that the claimed mechanism matters in a less abstract isolated cyber environment.

Agent-coordination venues such as AAMAS are a natural candidate because the [scope includes coordination, generative-agent evaluation, and simulation validation](https://cyprusconferences.org/aamas2026/call-for-papers-main-track/). A top-conference target is a quality goal; implementing these features cannot guarantee acceptance.
