# Sustained mission complexity checkpoint

4 October 2026. Delivers bounded T12d physical mission primitives on the CC4
adapter. This is software acceptance; Phase 3 calibration, hypothesis experiments
and live LLM qualification remain pending.

## Configure and inspect

Use `configs/cc4-mission.json`, or select CC4 and open **Mission duration and
objectives**. The example combines two named targets, a five-tick simultaneous
hold and deadline t250 with the existing segmented route and temporal modules.
It uses monitor defense; monitor does not restore. Select bounded observed
restoration separately when testing recovery. Initialize creates a paused world
at tick 0. Editing settings applies to a new episode.

`scenario.mission` is an optional schema-1.0 module. Omitted/null preserves
immediate privileged-access scoring. CC4 supports:

| Setting | Valid values | Meaning |
| --- | --- | --- |
| `hold_ticks` | 1–1000, default 1 | Final consecutive ticks with all targets privileged and all objective holds complete. |
| `deadline_tick` | null or 1–10000 | Absolute episode deadline, including the named tick; null uses the ordinary episode horizon. |
| `objectives` | 0–16 entries | Empty means one default all-target group; explicit groups cover exactly the mission target set. |
| Objective `id` | unique identifier, 1–48 characters | Saved progress label; it does not grant or unlock an action. |
| Objective `targets` | 1–12 unique target names | Hosts requiring current privileged access. |
| Objective `requires_privileged_hosts` | 0–12 unique native server names | Additional live physical access requirements, disjoint from that objective's targets. |
| Objective `hold_ticks` | 1–1000, default 1 | Consecutive samples satisfying both target and prerequisite access. |
| Objective `deadline_tick` | null or positive episode tick | Group must be complete by this tick and remain valid through final success. |

Schema validation rejects unknown fields, duplicate IDs/host lists, missing or
extra objective targets, unavailable prerequisite hosts, hard-dead-end
prerequisites, impossible hold/deadline arithmetic and deadlines beyond the
episode horizon. These checks do not prove general route/defense solvability.

## Exact scoring semantics

The engine aggregates **active root/SYSTEM sessions across the red team** from
native state after the complete joint tick, including defender end-turn effects.
Reports, claims, historical observations and inactive sessions cannot satisfy
the predicate. Team size and organization do not change this scoring definition.
Public mission requirements enter worker/coordinator inputs equally; confirmed
global progress remains researcher evidence.

Tick 0 never earns hold credit. Every later tick is sampled once. Re-reading
score at the same tick does not increment a counter. A missing required host
resets the affected objective to zero, even after that group previously
completed; loss of final readiness resets the global hold. Best hold and reset
counts remain saved. Objectives evaluate in parallel from physical state.
An objective prerequisite is a live host requirement, not a dependency on a
completed report or another stage ID. It adds no artificial native attack lock.

Final hold begins on the same tick that the last objective becomes complete.
For example, a two-tick objective and three-tick final hold require four
consecutive eligible samples. At a deadline, success is evaluated before failure,
so completing the requirement exactly on the final tick succeeds. A group
that becomes incomplete after its deadline fails immediately; expired deadlines
are not extended by recovery. Failure is sticky and ends the episode as
`mission_deadline` or `objective_deadline`; successful completion ends it as
`mission_success`. Other existing terminal conditions remain available.

Defenders continue acting during holds. Native Restore can remove required
sessions, reset progress and leave a legal recovery opportunity. Repeated
responses, tight budgets and route interactions can still make a particular
configuration infeasible. No automatic access repair is added.

## Code, evidence and UI boundaries

- `packages/contracts/missions.py` defines strict controls. The registry resolves
  the module and mission settings in the saved manifest. JSON, API, CLI and UI
  use generated contracts.
- `packages/engine_worker/missions.py` is a pure tick monitor, integrated by the
  CC4 runtime. No upstream CC4 source is modified. Native world hashing remains
  physical; mission differences are recorded in config/condition hashes and the
  resolved module manifest.
- `backend/app/runs.py` stops at real success/failure and persists the final
  frame. Worker and coordinator prompts receive requirements, not true counters.
- `backend/app/evaluation.py` records mission formula version 1.0, final/best
  hold, global/objective resets, deadline and structured failure. Scalar counters
  are included in CSV; full definitions, failure and events remain in JSON/ZIP.
  Existing success-time censoring and comparison exclusions remain in effect.
- `MissionEditor` controls duration, deadline and physical objective groups.
  `MissionEvidence` shows confirmed truth progress, missing requirements,
  resets, events and deadlines from saved frames. Private projection lists only
  that worker's owned privileged access and public requirements; it omits team
  counters and other workers' sessions. This is a view/input boundary, not an
  authentication boundary against the local researcher.

## Software qualification

The complete suite passes **101 Python tests**. **Eight frontend logic checks**
and the production build pass. Commands:

```powershell
./.venv/Scripts/python.exe -m pytest -q --junitxml=.local/mission-acceptance.xml
node --experimental-strip-types --test frontend/tests/research-ui.test.mjs
npm run build --prefix frontend
```

Nine mission cases check simultaneous multi-target holds, same-tick idempotence,
missing-tick rejection, revocable live prerequisites, inclusive mission and
objective deadlines, sticky failure, strict configuration and architecture-neutral
compilation. Native fixtures reach two real targets; another observes sensor-driven
Restore during a hold and legally reacquires the target before finishing.
RunManager fixtures persist deadline failure and a real prerequisite/objective
mission, close the engine at termination, preserve censoring and check CSV.
Forged report memory does not grant native success. No live model is called.

Browser checks cover enabling/disabling sustained scoring, invalid hold/deadline
settings disabling initialization, adding/editing/removing objective controls,
researcher hold replay and private view omitting team counters. A copied,
manually intervened exploration fixture remains excluded from comparisons:
`527dcdbd6e3a4f369e8844b9ff939221`, completed t18. Its t17 frame shows final
hold 2/3 and the live contractor prerequisite.
[Verified replay screenshot](../screenshots/mission-hold-software-replay.png).

A separate two-target mission is ready at t0 on the local preview service:
`9216af6de5e445b29434da285b0dd6fe`, hierarchy/four workers, monitor defense,
two route layers/two alternatives/dead ends, hold 5/deadline 250.
No Step or Run was issued for this environment.
[Initialized screenshot](../screenshots/mission-initialized-workbench.png).

## Remaining research boundary

These are sampled privileged-access objectives, not real-time session continuity,
data exfiltration, service disruption, patch/isolation workloads or arbitrary
business dependency DAGs. Durations/deadlines are synthetic controls. General
solvability, sequential/parallel opportunity diagnostics and a calibrated
complexity ladder remain unqualified. No LLM advantage, realism validation or
hierarchy/swarm research result is established.

Next: T12f diagnostics and stronger baselines, followed by live-model
qualification and authorized calibration before research experiments.
