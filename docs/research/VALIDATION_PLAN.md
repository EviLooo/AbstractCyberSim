# Mission and organization software qualification

**5 October 2026 plan-only revision:** future evidence-dependent qualification
uses [revised-plan A1–A10](REVISED_GRADUATION_PLAN.md#12-acceptance-prove-decision-structure-before-studying-performance).
Paired diagnostic, capability/credential, changed-condition and delivered-team
evidence gates are not yet implemented or passed. They supplement, rather than
reinterpret, the historical software fixtures below. No tests/runs/live calls
were performed for this revision; broad performance sweeps remain later work.

Later bounded checkpoint: [observed search and wider route qualification](OBSERVED_SEARCH_ACCEPTANCE.md)
adds planner correctness/privacy/coordination checks and selected physical
composition witnesses. It does not establish research difficulty or universal
solvability. Earlier counts below are historical.

5 October route-tradeoff extension: [native service/time/privilege and sensor
acceptance](ROUTE_TRADEOFFS_ACCEPTANCE.md) adds bounded physical effects, private
clues, denial/release, deadline outcomes and saved workbench evidence. See the
[completion ledger](COMPLETION_LEDGER.md) for requirements still open. Historical
counts below document earlier checkpoints, not closure of Phase 3.

4 October 2026. Acceptance gates for the legacy workbench before custom
research scenarios and live LLM qualification. The initial mission milestone
covered T01/T03 and portions of T07–T10. The subsequent
[Phase 1–2 gate](PHASE_1_2_ACCEPTANCE.md) closes T04–T10 within the enabled
legacy/scripted scope; broader engine and scientific qualification remain pending.

The subsequent [CC4 adapter acceptance](CC4_ADAPTER_ACCEPTANCE.md) adds a
separate unmodified Python 3.12 backend. Its 14 bounded checks cover actor
ownership, native durations, observed restoration, complete controlled-service
missions, API artifacts and population settings. The full 61-test regression
and two subsequently added checks passed; five frontend checks and the production
build passed. The legacy evidence below remains specific to its original gates.

The [sustained mission checkpoint](MISSION_COMPLEXITY_ACCEPTANCE.md) adds nine
bounded cases. The complete current regression passes **101 tests**, with
**eight frontend checks** and a passing build. It qualifies sampled simultaneous
holds, inclusive deadlines, live privileged-host prerequisites, native Restore
during dwell, legal recovery, persistence and private mission projection.
Earlier counts below remain historical checkpoint evidence.

The [baseline/diagnostic checkpoint](BASELINE_DIAGNOSTICS_ACCEPTANCE.md) adds
fifteen cases. The complete current regression passes **116 tests**, with
**nine frontend checks** and the build. Local-information policies complete
bounded C0/C1/C2 development cells; organization traces, private projection,
source choice, loss/recovery and hand-counted diagnostics are checked.
This does not establish a scientifically calibrated complexity ladder.

## Execution boundary

The subsequent [temporal-module checkpoint](TEMPORAL_COMPLEXITY_ACCEPTANCE.md)
adds 17 bounded checks over the CC4 layer. The complete current regression passed 80 tests.
Six frontend tests and the build pass. This is now a historical checkpoint;
the [segmented route checkpoint](ROUTE_COMPLEXITY_ACCEPTANCE.md) adds twelve
checks, bringing the full regression to **92 passed**, with **seven frontend
checks** and a passing build. It qualifies native ACLs, explicit pivots,
restoration/alternate-source recovery and private organizational pipelines.
Legacy/adapter gates below retain their
historical counts and scope; none is a scientific experiment.

All acceptance runs are pytest fixtures in temporary storage. They use scripted
or mocked cognition, never an installed model, evaluation matrix, hypothesis
comparison, or the researcher's `artifacts/` directory. A passing fixed fixture
is evidence of software behavior, not general solvability, simulator realism,
or an advantage for either organization.

Service: Python 3.13.9. Native worker: Python 3.8.11, Gym 0.23.1, NumPy 1.21.6.
CybORG revision: `2742b5e0ce4330c9b14006b38acd3b5ebe00d6fd`, with the existing
two-line actor-owned Portscan patch. No additional vendor changes are required.

## Fixed complete-mission fixture

`tests/test_mission_qualification.py` specifies:

| Setting | Value |
| --- | --- |
| World | Fresh native Scenario2, world seed 7 |
| Teams | Hierarchy, swarm, independent; worker counts 1, 2, 8 |
| Goal | Active root/SYSTEM access to **both** Enterprise2 and Op_Server0 |
| Defense | Native end-turn Monitor; no removal/restoration |
| Cognition | Scripted, zero provider calls |
| Schedule | Per-worker joint ticks, schedule seed 27, maximum 100 ticks |
| Transport | Seed 17, no added delay/loss, normal configured capacities/TTL |
| Intervention | None; policies act from own observations and delivered intel |

The tested attack progression is discovery in the known User subnet; scans of
observed addresses; native service exploitation; escalation/inspection of owned
footholds; learning Enterprise addresses from host intel; Enterprise discovery
and acquisition; inspection of Enterprise2 to reveal the operational-server
address; scan/exploitation of that server. Different workers can contribute to
the team goal. The policies do not receive a privileged hostname-to-IP map or
an oracle path. Native exploit selection and seeded ordering can change which
particular route a worker follows, so a hard-coded action sequence is not the
acceptance criterion.

Every fixture must reach `mission_success` within its bound, close the child
process, and preserve zero manual interventions/provider calls. Every saved
tick must count target access once, require all targets, advance the native
step counter exactly once, execute each non-Sleep worker action once, and run
Monitor once at end of turn. Native Sleep is filtered from execution and has
UNKNOWN outcome; it is not invented as an executed action in the trace.

These nine tests are engineering coverage, not nine research trials. They
produce no architecture rankings or confidence intervals. Count 4 remains
covered by the separate native discovery/scan/exploit ownership fixture.

## Boundary and organization fixtures

| Fixture / source | Setup and stimulus | Required result |
| --- | --- | --- |
| Native boundaries: missing controller | Scan with session 999 | Gateway rejection, UNKNOWN/Sleep, no new access |
| Native boundaries: ownership | Red_0 acquires User1; try its remote-session ID as controller for either worker | Neither a peer's ID nor an owned reverse shell supplies a native controlling session |
| Native boundaries: peer escalation | Red_1 knows User1 but owns no foothold there | Escalation rejected; knowing an address is insufficient |
| Native boundaries: mission privilege | Red_0 exploits User1, then escalates it | Low privilege does not satisfy the goal; active SYSTEM/root does |
| Native boundaries: inactive foothold/controller | Explicitly deactivate a target session, then the controller | Goal becomes false; inactive target escalation and inactive-controller scan rejected |
| Native boundaries: actor binding | Submit a Blue key to the red-action gateway | Request rejected before tick advance |
| Native boundaries: no physical route | Cut all graph edges incident on User1 immediately before scanning, or after its scan before exploitation | Native FALSE, no cache/session grant, no crash |
| Native boundaries: legacy operational gate | Reveal Op_Server0 address to both workers; acquire Enterprise1 only for Red_1 | Red_0 remains blocked; Red_1 can scan the operational target |
| Existing engine bridge fixtures | Initialize 1/2/4/8 actors, discover, scan, exploit | Own sessions for each actor; controlled-host counts deduplicated |
| Existing evidence fixture | Forge evidence origin, then deliver an authentic observation | Forgery grants nothing; verified intel adds address knowledge without scan cache/session grants |
| Organization: privileged inspection | Private memory contains an already privileged remote Enterprise2 foothold | One inspection candidate, not one per duplicate session; successful inspection is not repeated |
| Organization: branching task allocation | Deliver two workers' candidate reports for two scan targets | Distinct assignments; no worker action before assignment delivery; recipient's actual controller ID used |
| Organization: local scan completion | Red_0 reports a successful scan; Red_1 still needs that scan | Red_1 remains assignable; Red_0 completion does not populate Red_1's cache |
| Organization: decentralized tie | Red_1 has one candidate; enqueue Red_0 claim before delivering it | Red_1 acts before delivery, yields after delivery, and can act again after claim TTL |
| Organization: seeded transport | Broadcast recipient copies with loss probability .5, seed 19 | Reproducible full message log, charged copies, resolved states, delivery strictly after creation |
| Organization: total loss | Three joint ticks with loss probability 1 in all three architectures | Hierarchy leader stays blind and workers wait; swarm/independent can act locally; independent has no messages |
| Organization: malformed authority | Mock a hierarchy worker proposing an unassigned scan | Proposal retained as invalid, native Sleep/UNKNOWN, invalid metrics incremented |
| Organization: private cognitive inputs | Only Red_0 discovers; drop all messages; capture mock worker inputs | Red_1 never receives that discovered address; no truth channel in worker inputs |
| Controls: pause/continue | Compare five single steps with background execution paused at tick 4 then stepped once | Same world, actions, observations, views, physical effects, messages and execution traces |
| Controls: tick limit | End an unsolved mission after two ticks | `tick_limit`, censored success time, closed native process; further stepping rejected |
| Existing controls/storage/provider fixtures | Invalid actor/config/origin, restart, replay, manual evaluation override, mocked format repair/budget/transport failure | Declared rejection and lifecycle behavior; saved records remain readable; usage charged |

Native boundary setup is isolated in `tests/native_boundary_fixture.py`, launched
with the engine interpreter. Address revelations, session deactivation and
graph cuts are explicit privileged **test setup**, not production APIs, legal
agent decisions, or qualified new scenarios. The operational check verifies the
legacy hostname rule, not a realistic firewall or a generic four-zone policy.

## Reproduce and inspect

From the project root:

```powershell
./.venv/Scripts/python.exe -m pytest -q
```

Result at the initial mission gate on 4 October: **38 passed**. The subsequent
Phase 1–2 acceptance gate has **49 passed**, plus **4 frontend logic tests**
and a successful production build; see [the acceptance checklist](PHASE_1_2_ACCEPTANCE.md).
Saved fixture configs, worlds, frames,
messages, metrics and engine logs live under the pytest temporary root. The
ordinary replay interface can display those same frames without running an
agent. Do not copy them into the evaluation dataset or label them paper results.

In-app browser verification replayed the completed two-worker hierarchy fixture
from its temporary store: initial state 0/2 privileged targets, final state 2/2,
both mission nodes visibly privileged, final native exploit TRUE, star
communication view, and disabled execution controls for the closed run.
The [saved screenshot](../screenshots/complete-mission-software-fixture.png)
is software acceptance evidence, not a research result. The temporary replay
service was separate from the researcher's live workbench.

Additional upstream regression, using the Python 3.8 interpreter from the
`CybORG/` directory:

```powershell
python -m pytest CybORG/Tests/test_sim/test_Actions/test_RedActions/test_RedAbstractActions/test_DiscoverRemoteSystems.py CybORG/Tests/test_sim/test_Actions/test_RedActions/test_RedAbstractActions/test_DiscoverNetworkServices.py CybORG/Tests/test_sim/test_Actions/test_RedActions/test_RedAbstractActions/test_ExploitRemoteService.py CybORG/Tests/test_sim/test_Actions/test_RedActions/test_RedAbstractActions/test_PrivilegeEscalate.py -k 'success or num_hosts' -q --disable-warnings
```

Result: **55 passed, 24 skipped, 526 deselected**. The skipped exploit success
and host-count tests are decorated `skip` upstream; they provide no evidence.
Our native exploit integration and complete-mission fixtures provide the
checked exploit evidence. Remaining upstream tests were not run by this command.
Existing deprecation warnings remain in the pinned engine.

## Corrections established by these fixtures

1. A privileged remote session still needs native `PrivilegeEscalate`'s
   `ExploreHost` behavior to learn onward addresses. Skipping it deadlocked
   the single-worker mission after acquiring Enterprise2.
2. The coordinator tracks completed actions by reporting actor. A successful
   peer scan does not complete a recipient's required local cache.
3. Assignments bind the recipient's reported active controller instead of
   assuming every controller ID is zero.
4. The gateway requires an active target foothold before escalation.
5. Frames include the native step counter; execution traces retain native
   Sleep filtering and end-turn behavior.

## Remaining qualification and next milestone

This gate covers the fixed legacy mission and the listed boundaries. The
subsequent Phase 1–2 gate adds scheduled communication-link interruption,
sparse directed topology, knowledge provenance/relay attacks, observed action
changes, CLI parity, and UI refresh/reconnect qualification. T04–T10 are accepted
within that enabled legacy/scripted scope. Full native exploit
coverage, broad seed solvability, generic NACL/block/bandwidth semantics,
inactive Enterprise sessions in the inherited operational gate, active defense
and recovery are not established here. Native operational permission checks
the existence of an Enterprise-named actor session and does not inspect its
active flag; qualify/replace that rule before using recovery defense.

The next construction milestone is **Phase 3 / T12a–T12b**: profile contracts,
compiler, qualified generic linear/branching worlds and native reachability.
Then T12c/T12d/T13a adds observations, missions and bounded reactive recovery;
T12e/T12f connects UI controls and diagnostic baselines. Follow
[the revised complexity design](ENVIRONMENT_COMPLEXITY_DESIGN.md).
T11 live-model qualification remains separate and requires explicit
authorization for model calls. Research pilot/freeze work remains in T17 and
requires authorization for experiments.

## Planned Phase 3 gates — not yet executed

The following are required future fixtures, not additions to the current 49-test
qualification count. Keep every native check in isolated temporary storage.

| Gate | Required assertion |
| --- | --- |
| Module contract and composition | Invalid dependencies/ranges/unqualified IDs rejected before initialization; declared supported combinations work; disable/no-op parity and fresh-world reset. |
| Generation and physical access | Materialized static world reproducible; alternative route succeeds with owned active access; denied source/service/policy/privilege path fails without a crash; no hostname bypass. |
| Service change | Compatible vulnerable variant succeeds where qualified; version-specific patch prevents the affected native technique; repeated attempts do not undo patch; cache/registry revisions consistent. |
| Evidence privacy and refresh | Mutating undisclosed state leaves prompts/candidates identical; old report stays old; a legal re-observation reveals only permitted new facts; no automatic cause disclosure. |
| Native recovery | Removal/restoration tested for all red actors on a host and native PID/session registries; controller loss and alternate-controller behavior; false evidence cannot restore removed access. |
| Isolation versus restoration | Isolation changes remote reachability while preserving explicitly modeled persistence; restoration applies documented host/session effects; unisolation does not fabricate new access. |
| Defender causality | Defender decisions depend only on its observations; event signal/decision/effect times honor delay/cooldown/budget; it cannot react to a not-yet-executed action; one defender turn per world tick. |
| Mission/dwell | Actual target access required; dwell increments and resets correctly under loss; recovery deadline and infeasible conditions distinguished; report text never completes physical dependencies. |
| Reactive versus scheduled change | Scheduled events identical for matched schedules; reactive policy/version matched but effect history follows attacker-specific observations; no architecture-specific targeting. |
| UI/replay/config | Preset expands to saved resolved values; toggles affect new runs; truth events and worker symptoms differ; event timelines/dwell/evidence ages reconstruct offline. |
| Optional durations/deception/user activity | Busy actions cannot double-execute; native ordering pinned; decoys/noise disclosed only by legal evidence; user activity cannot silently create attacker footholds. |

Behavioral validation is a separate T17 dossier: mechanism/source/assumptions,
expert trajectory review, uncertainty sensitivity and optional isolated-system
comparison. Passing these software fixtures does not validate human realism or
establish LLM/organization superiority. Development calibration must retain
competent rule/replanning and single-agent controls, then freeze the held-out
suite before final results are inspected.
