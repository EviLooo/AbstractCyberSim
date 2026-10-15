# CC4 compatibility audit and backend decision

Follow-up: [the adapter is now implemented and selectable](CC4_ADAPTER_ACCEPTANCE.md).
The audit below records status at audit time; that implementation checkpoint
supersedes its migration proposal.

4 October 2026. Decision: **target CC4 for the complex research backend**, through
a separate adapter and custom scenario generator. Retain the accepted legacy
backend for regression fixtures and existing runs. Do not replace its dependency
in place. This audit changes the proposed build order; migration is not implemented.

CC4 supplies more of the required behavioral mechanisms than the installed
legacy scenario. We do not need to build a simulator from scratch. Its stock
defensive benchmark is not the offensive hierarchy-versus-swarm study, however.
The workbench must still implement private beliefs, team communication,
organizational policies, independent offensive missions and evaluation.

## Inspected version and local setup

Repository: [CAGE Challenge 4](https://github.com/cage-challenge/cage-challenge-4).
Inspected commit: `8c3c50ca54b176c2de199847944e8dcc035497e3`.
The audit checkout is `.local/cc4-audit/checkout`; it is unmodified and ignored
by the parent repository. Python **3.12.5** is isolated in
`.local/cc4-audit/.venv`. No cloud, GPU, simulator emulation or provider was used.
This establishes local feasibility of the simulator fixtures, not future LLM
throughput on this laptop.

The [upstream installation instructions](https://github.com/cage-challenge/cage-challenge-4/blob/8c3c50ca54b176c2de199847944e8dcc035497e3/documentation/docs/pages/tutorials/01_Getting_Started/1_Introduction.md)
recommend Python 3.10 or later, a virtual environment, full Requirements.txt,
and an editable installation. For this simulator-only audit we deliberately
installed a smaller dependency set, retaining relevant upstream pins, and loaded
the checkout directly through the probe's Python path. The full Ray/Torch/RL
training stack and upstream editable package installation were not performed.
[The resolved audit lock](../../engine/cc4-audit.requirements.lock) records every
installed package; it is not the production engine lock.

The selected upstream pytest command could not collect tests: CC4's conftest
imports its wrappers package, which eagerly imports `EnterpriseMAE` and requires
`ray.rllib`. **No upstream tests are claimed passed.** We did not fake that import
or edit upstream tests. Instead, [our probe](../../tools/audit_cc4.py) exercises
the native API directly. All **nine bounded compatibility fixtures passed**;
[machine-readable evidence](cc4-audit.json) records versions, stock/custom
distinctions and outcomes. These are software checks, not hypothesis experiments.

To reproduce in PowerShell, from the repository root after cloning the pinned
checkout (or use the checkout already present):

```powershell
git clone https://github.com/cage-challenge/cage-challenge-4.git .local/cc4-audit/checkout
git -C .local/cc4-audit/checkout checkout 8c3c50ca54b176c2de199847944e8dcc035497e3
& 'C:\Program Files\Python312\python.exe' -m venv .local/cc4-audit/.venv
& .local/cc4-audit/.venv/Scripts/python.exe -m pip install -r engine/cc4-audit.requirements.lock
& .local/cc4-audit/.venv/Scripts/python.exe tools/audit_cc4.py --checkout .local/cc4-audit/checkout --output .local/cc4-audit/probes.json
```

## What works, and what it actually means

| Requirement | Evidence and implementation implication |
| --- | --- |
| External simultaneous attackers | Native `parallel_step(actions=...)` accepts multiple actor actions. Custom 1/2/4/8-worker fixtures discover in one joint tick, scan and acquire independently owned target sessions. The network remains 90 hosts in these fixed-seed checks. |
| Adjustable team size | Stock code creates **six red identities**, covering eight non-internet zones, with one initially active. A custom generator can clone workers with equal footholds, per-worker end-turn hooks and all-zone allowed-subnet lists. Counts beyond eight remain unqualified. |
| Mobile independent ownership | Stock traversal transfers a new session to the zone's attacker and gives that attacker an observation. In the custom generator fixture, the originating worker retains a cross-zone session, and the other worker does not automatically learn its target. No controller patch was needed for these paths. |
| Private technical knowledge | A worker's scan populates its own session port cache; another worker's cache remains empty. Address discovery is not automatically shared in the custom fixture. Raw action spaces still include unknown addresses with `False` flags: the adapter must filter those keys. |
| Delivered intelligence | A minimal, proven Interface update makes a recipient's scan eligible without granting sessions or ports. Only the subsequent native scan populates ports. Provenance, delay/loss and message accounting remain workbench responsibilities. |
| Action durations | Joint exploit attempts take the stock four ticks; Restore takes five. Submit an action once and wait while busy. Do not advance the world separately per worker. |
| Real defender effects | Native Restore removes the target's red sessions. Native BlockTrafficZone denies service discovery; AllowTrafficZone makes it succeed again. Sleep policies do not remove automatic end-turn hooks such as blue Monitor and red session checks. |
| Changing mission policy | A nine-tick fixture follows phases 0/1/2, changes Green's allowed-subnet lists and leaves actual firewall blocks unchanged. Phase policy is intended communication policy; physical enforcement needs native defender actions or explicitly scheduled transitions. |
| Benign users/deception | Native Green actions, phishing, decoys and detection exist in source/docs. Their full interactions with our custom workers are **not runtime-qualified** in this audit. Keep off until dedicated fixtures qualify them. |
| Offensive objectives | Native Red reward uses EmptyRewardCalculator. Blue rewards measure defensive operational performance. Retain an independent, versioned offensive mission evaluator; do not use negated Blue reward as a substitute for our mission. |

Exploit attempts can fail under native stochastic technique selection. The
worker fixtures allow at most four attempts and record every TRUE/FALSE outcome;
they do not assert success on every attempt or estimate success probabilities.
The fixed contractor foothold is deliberately separate from the target so that
an initial session cannot be mistaken for successful new compromise.

Source anchors: [red generation and rewards](https://github.com/cage-challenge/cage-challenge-4/blob/8c3c50ca54b176c2de199847944e8dcc035497e3/CybORG/Simulator/Scenarios/EnterpriseScenarioGenerator.py#L751),
[zone ownership transfer](https://github.com/cage-challenge/cage-challenge-4/blob/8c3c50ca54b176c2de199847944e8dcc035497e3/CybORG/Simulator/SimulationController.py#L820),
[mission policy update](https://github.com/cage-challenge/cage-challenge-4/blob/8c3c50ca54b176c2de199847944e8dcc035497e3/CybORG/Simulator/SimulationController.py#L747),
[exploit selection and duration](https://github.com/cage-challenge/cage-challenge-4/blob/8c3c50ca54b176c2de199847944e8dcc035497e3/CybORG/Simulator/Actions/AbstractActions/ExploitRemoteService.py#L42).

## Modular implementation handoff

1. **Add an isolated CC4 worker and adapter before T12.** Pin/register the new
   dependency separately from the existing CybORG submodule. Keep the service/UI,
   communication transport, coordinator/worker policies, artifacts and reducers.
   Map logical worker names to CC4 names at the boundary. The constructor API,
   session module paths, action names, pending actions and snapshots differ;
   copying the existing worker or replacing its imports is insufficient.
2. **Build a production research generator from the proven configuration hook.**
   Give each worker its own starting session and all-zone mobility; preserve
   actor-bound end-turn checks and native physical blocks. Explicitly account for
   changed foothold assumptions. Verify loss of initial access, inactive workers,
   reset, controller routing, overlapping workers and composed defenses. The
   audit-only generator has not qualified these broader cases. Native phishing
   and respawn logic require an explicit policy when several workers share zones.
3. **Qualify C0/C1 before enabling C2 changes.** Initially retain CC4's native
   enterprise zones and service templates. Arbitrary zone counts, business
   dependency graphs and our proposed generic topology compiler still require
   code. Expose only supported profiles through a capability registry.
4. **Reuse native mechanisms in T12/T13.** Build bounded defender policies over
   their observations, with response budgets, delays and cooldowns. Use native
   restore/block/allow/decoy effects where qualified. Add service/version patching
   only as a separately tested extension. Default Monitor alone is not adaptive
   defense. Intended policy and actual connectivity must be separate UI fields.
5. **Adapt the action loop and UI.** Represent busy actors, remaining duration,
   completion outcomes, session/privilege loss, firewall effects and evidence
   age. Render native changes through the existing replay/event pipeline. Extend
   versioned contracts and validate capability combinations before enabling them.
6. **Keep missions and scientific controls in the research layer.** Physical
   multi-target/dwell criteria, stale private beliefs, communication budgets and
   hierarchy/swarm evaluation remain independent of CC4's defensive reward.
   Freeze configurations and validate fair budgets before any approved pilot.

The action model remains abstract: ExploitRemoteService chooses a concrete
technique internally from scanned ports. To study reasoning about technique
choice, qualify a narrow selector/action extension using observed prerequisites.
CC4 alone does not supply rich identity/credential lifecycles, arbitrary
environment evolution or proof that LLM agents outperform strong baselines.

## Gate before switching the workbench

Preserve legacy complete-mission/replay fixtures. Pass CC4 adapter contract and
complete offensive-mission fixtures, own-session/privacy checks, deterministic
fresh-world checks, action-duration accounting, defender observation/effect
tests, communication provenance and artifact/replay round trips. Qualify count
and complexity combinations in the capability registry. Only then enable CC4
in the workbench. Existing legacy runs remain identifiable and replayable;
raw legacy and CC4 rewards/results are not directly comparable.

The current application, Python 3.8 engine environment and paused researcher
session were not migrated or restarted during this audit. Phase 3 remains pending.
