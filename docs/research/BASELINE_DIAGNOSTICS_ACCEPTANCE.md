# Local baselines and decision diagnostics

Later checkpoint: [observed search acceptance](OBSERVED_SEARCH_ACCEPTANCE.md)
adds `local_search` version 1.0 and shared tracker version 1.2. The older policy
semantics and fixture counts below remain historical.

Later route extension: [route-tradeoff acceptance](ROUTE_TRADEOFFS_ACCEPTANCE.md)
records policy version 1.1, which uses observed service-assessment time estimates.
The original 1.0 fixture scope below remains historical. The heuristic is still
not a risk-optimal or globally optimal path planner.

5 October 2026. Delivers the bounded software portion of T12f: two versioned
local-information policies, shared state tracking, decision evidence and
structural/behavioral diagnostics. Live LLM controls and broad scenario
calibration remain pending. The main study is still hierarchy versus swarm LLM
teams; these baselines diagnose where coordination and adaptation matter.

## Researcher controls

Choose **Scripted** and select **Decision policy**:

- **Original scripted policy** preserves the historical default.
- **Local rules** follows fixed technical priorities, then owned source and
  observed mission-host preferences.
- **Local replanning** revisits observed action frontiers using mission evidence,
  source-specific scans, failures, evidence age and optimistic action costs.

`cognition.scripted_policy` accepts `legacy`, `local_rules`, or `local_replan`;
default is `legacy`. Non-legacy choices require the scripted provider. Switching
the UI to Ollama resets this field to legacy. No provider is called during
configuration or initialization.

`cognition.action_retry_limit` accepts 1–20 (default 2).
`cognition.failure_backoff_ticks` accepts 0–100 (default 0). Candidate generation
uses these settings for every provider. The development fixtures use 3 attempts
and 3 ticks of backoff for both new policies. Backoff starts at the observed
failed completion, not the first tick of an in-flight exploit. A worker's
observable access loss advances its knowledge epoch and allows recovery attempts.
Successful actions are suppressed within an epoch; stale scans can be refreshed.
Settings are recorded in config and included in the condition fingerprint.

These are candidate/search controls. They are not new native network rules or
a hard retry enforcement mechanism on every LLM-generated proposal. Native
ownership, source cache, private evidence, organization and schedule checks
remain the execution gates. Hold this distinction constant in final comparisons.

Ready examples: `configs/cc4-local-rules.json` and
`configs/cc4-local-replan.json`. Both use one independent worker, two targets,
one gateway layer/two alternatives/dead ends, controlled SSH services, passive
defense and a three-tick hold. They initialize paused. New policy software
qualification is for CC4; applying them to legacy is not qualified. The original
legacy policy remains the accepted default there.

## State tracking and strategy are separate

`backend/app/baselines.py` contains `LocalStateTracker` and `BaselinePolicy`,
version 1.0. Neither imports the simulator or reads world/truth snapshots.

The tracker remembers owned controllers, locally disclosed address/name
relationships, first-seen address ticks and observed failed action counts.
Native inventory can identify a host by the observation's host-name key without
repeating `System info/Hostname`; this is usable observed evidence. An address
must still be in that worker's disclosed native knowledge. It does not turn an
unobserved IP into an allowed parameter or a report into access.

`PrivateMemory.public_view` exposes a `local_state` snapshot of these remembered
facts to **all providers**, including the eventual LLM, and saves it in private
frames. Busy actions and duplicate history reads do not repeatedly increment
failures. Epoch changes clear obsolete failure counts. Historical host knowledge
remains a belief; actual access comes from active owned native sessions.

The rule policy favors escalation/inspection, deployment, exploitation, scanning
and discovery, with stale refresh before further exploitation. The replanner
first finishes owned footholds, then favors identified mission hosts, observed
successful service scans and sources without failed scan evidence. It includes
estimated action/remaining costs when ranking unresolved frontiers. A newer
pivot is not automatically a better source. Multiple eligible choices and the
selected action are recorded.

CC4 cost estimates are discovery 1, scan 1, exploit 4, escalation/inspection 2
and pivot deployment 2 ticks. Estimated remaining steps are optimistic. These
are not probabilities, guaranteed route times, A* shortest paths over an unknown
network or measured optimal strategies. Real native durations/outcomes continue
to be recorded independently. The environment itself is unchanged: alternative
gateways can still have equivalent costs, and exploit technique selection stays
inside native CybORG.

Workers hold when their own active privileged sessions cover all public targets
and prerequisite hosts. They cannot infer team-wide completion from this check.
Native mission scoring remains responsible for real team success.

## Organizations and resource boundaries

The same worker policy is usable with independent, hierarchy or swarm teams.
Independent workers use private observations. Swarm keeps delivered-claim
coordination and deterministic tie breaking. Hierarchy waits for delivered
assignments; its coordinator orders candidates from delivered reports, preserves
source ownership and avoids rebinding a worker's ranked source-dependent frontier
to another worker. Delivered verified intel can still enable the recipient's
own subsequent scan. No live tracker, peer cache or hidden global route plan
is consulted by the coordinator.

Scheduling, busy-state admission, communication capacity and provider budgets
continue through the existing runner. The two new policies make no model calls.
The existing one-worker independent and multi-worker independent configurations
provide the structural controls for later LLM qualification. No single-LLM or
multi-LLM performance result is claimed here.

## Saved evidence, UI and exports

`backend/app/diagnostics.py` has no role in cognitive decisions. Researcher-only
structure describes materialized gateway widths/combinations, targets, admission
capacity, defender mode, observation delay and mission duration. It explicitly
does not infer difficulty, distinct path costs or recovery solvability.

Behavior counters are recomputed from saved decisions, actions and delivered
messages: multiple-choice/changed-state/holding decisions, completed failed
actions, successful completed scans, source switches, assignments and claims.
An in-flight continuation is not a second completed action; repeated message
snapshots do not count one delivery again. Version is 1.0.

Frames save `decisions` and `diagnostics`; the manifest saves policy descriptor
and structural settings. Each decision identifies its actor, public goals still
missing from own access, state changes, up to twelve ranked alternatives, omitted
count, planning estimates, proposed action and schedule-admitted proposal.
Manual overrides are labeled. These records are policy evidence, not private
chain-of-thought or proof of reasoning. Native action rows remain the evidence
of actual execution.

The **Decision diagnostics** panel provides a readable choice/source/cost/failure
table, raw saved record and researcher structural/behavior details. Worker views
show only that worker's decision; they omit the structure, team counters and
other workers' choices. This is the existing local researcher/input boundary,
not user authentication.

CSV includes policy, diagnostic formula version and key behavior counts.
JSON/ZIP retain the full evidence. Recompute offline without an engine/model:

```powershell
$env:RESEARCH_DATA_DIR='C:\path\to\saved\store'
./.venv/Scripts/python.exe -m backend.app.cli diagnostics RUN_ID
```

## Bounded acceptance and remaining gates

`tests/test_baselines.py` contains fifteen cases: distinct informed rule/planner
choices, hidden-input invariance, tracker idempotence/loss handling, reachable
source preference, native inventory key evidence, private holds, shared retry
settings and hand-counted diagnostics; six native policy/cell cases and two
organization cases.

Development cells use seed 100 and controlled SSH services:

| Cell | Qualified fixture composition |
| --- | --- |
| C0 fixture | One target, one gateway route, passive defender, immediate evidence. |
| C1 fixture | Two targets, two gateway alternatives, hardened dead end, passive defender. |
| C2 fixture | C1 plus timestamped evidence (stale after 8), sensor-driven Restore (delay 12, budget 1 per native defender), 20-tick hold. |

Both policies complete each native fixture using their allowed inputs, without
manual actions or model calls. C2 explicitly checks actual defender completion,
own observable loss and recovered access. Restoration can occur before the final
hold begins; a hold reset is not required in every C2 trajectory. Separate T12d
fixtures qualify loss during a hold. Hierarchy and swarm fixtures complete with
two workers and produce distinct delivered assignment/claim traces.

These are software fixture names, not a scientifically calibrated C0–C2 ladder.
They do not cover all seeds, worker counts, route depths, observation delays,
defender budgets, model contexts or alternative exploit templates. Difficulty
need not increase monotonically. A passing rule policy is a useful control,
not grounds for changing the environment until an LLM is forced to win.

The complete regression passes **116 Python tests**, with **nine frontend
checks** and the production build. `.local/baseline-acceptance.xml` records
116 cases with zero failures/errors/skips. The CC4 checkout stays unmodified.

Browser checks verify policy selection, retry validation, readable choice/cost
tables and private views excluding structural/team diagnostics. Archived
exploration fixture `4f20ae99241f41279e81fafbfa7dcf42` completes at t71 with
zero model calls and carries `software_fixture=true`, excluded from comparison
by its exploration purpose. Its t46 frame shows a scan selected from the
previously useful owned source during recovery.
[Verified decision screenshot](../screenshots/baseline-recovery-decision.png).
Offline CLI output matches its saved behavior counters.

The preview at port 8794 has a fresh one-worker/two-target environment
`bb581c0a5757426cb203048a5e141007`, ready at t0, local replanning, passive
defense, hold 3, attempts 3/backoff 3. No Step or Run was issued.
[Initialized screenshot](../screenshots/baseline-initialized-workbench.png).

No research experiments were executed. Next gates:
T11 live-provider/model qualification, wider development scenario/calibration
checks, then authorized scientific evaluation.
