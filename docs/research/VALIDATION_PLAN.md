# Mission and organization software qualification

4 October 2026. Acceptance gates for the legacy workbench before custom
research scenarios and live LLM qualification. The initial mission milestone
covered T01/T03 and portions of T07–T10. The subsequent
[Phase 1–2 gate](PHASE_1_2_ACCEPTANCE.md) closes T04–T10 within the enabled
legacy/scripted scope; broader engine and scientific qualification remain pending.

## Execution boundary

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

The next construction milestone is **Phase 3 / T12**: qualified generic linear
and branching enterprise profiles, with explicit access prerequisites and
scripted legal-path/denied-shortcut fixtures. Extend this plan for each new
profile, then T13 recovery. T11 live-model qualification remains separate and
requires explicit authorization for model calls. Research pilot/freeze work
remains in T17 and requires authorization for experiments.
