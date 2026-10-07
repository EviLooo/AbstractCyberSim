# Observed-information search and wider route qualification

5 October 2026. Bounded software acceptance for the next T12b/T12f checkpoint.
The research comparison remains hierarchy versus swarm LLM attacker teams.
No research experiments, provider calls or model-performance claims were made.

## Delivered behavior

Select Scripted → **Local search · observed routes and deadline**. Existing
legacy, local_rules and local_replan policies keep their selection semantics.
`backend/app/search_policy.py` implements policy version 1.0. The shared fact
tracker in `baselines.py` is version 1.2; its added connection memory is exposed
to every provider in `PrivateMemory.public_view().local_state`.

The policy starts with locally eligible actions, then estimates scan, exploit,
escalation/inspection and pivot continuations. A known privileged-service hint
can remove unnecessary escalation when acquiring a goal; a gateway still needs
inspection and pivot deployment. Own successful service caches establish
directed source-host → target-address observations. Those facts remain
historical beliefs after access loss; they never restore a session/cache or
prove a connection is still open. Hypothetical subsequent hops rescan.

Bounded uniform-cost search retains Pareto labels for both time and score: a
fast, expensive route cannot be discarded just because a slower route has a
lower score. Search seeks the next observed missing goal. Where no path is
known, it ranks information frontiers. It replans after each available decision;
native busy actions continue without being interrupted by the planner.

Deadline-feasible estimated paths rank before late paths. Estimates reserve the
full public mission hold and applicable objective hold/deadline requirements;
team-confirmed progress is never used. If no discovered plan fits, a least-late
choice remains executable and is flagged. These are conservative planning
estimates, not a mission admission test or proof of feasibility.

Planning score is estimated ticks plus ordinal detection-risk, observed-failure
and unverified/stale-connection penalties. Low/medium/high exposure use ordinal
values 0/0.5/1; these are **not success or detection probabilities**. Scan and
exploit can independently trigger native sensor consequences; this simple
planning cost does not model their joint probability or predict Blue responses.
Only limited own/delivered assessments are read, never manifest ACLs, exact sensor
rates, route-pressure release times or true peer access.

`cognition.search` settings (saved, hashed and editable in UI/JSON):

| Setting | Default | Range |
| --- | --- | --- |
| risk_weight | 8 | 0–100 |
| failure_penalty | 6 | 0–100 |
| unknown_edge_penalty | 4 | 0–100 |
| max_expansions | 128 per candidate | 1–4096 |

Shared candidate retry/backoff settings remain separate. The search-tradeoff
example uses six attempts and eight ticks of backoff; they are development
settings, not scientifically tuned parameters. Search caps are saved as
`search_truncated`. Plans, scores, estimated ticks, uncertainty and warnings are
saved in decision alternatives; the UI shows the preferred plan and distinguishes
it from the action actually admitted by coordination/team capacity.

## Qualification evidence

`tests/test_search_policy.py` checks hand-counted risk/time choices, tight and
infeasible deadlines, exhaustive tiny-graph comparison, Pareto labels, caps,
public objective requirements, privileged-service hints, failure replanning,
hidden-input invariance, peer-access rejection, idempotence, remembered routes
after loss and shared provider information without transferred native caches.
Bounded autonomous native checks complete C0 with independent/hierarchy/swarm,
C1 with two goals/dead ends, C2 with native restoration/access recovery, and a
one-layer deterministic route-pressure case. They use no manual overrides or
model calls. They do not measure architecture performance or LLM advantage.

`tests/test_route_qualification.py` adds four fixed **legal witness** cells:

| World seed | Workers | Gateway layers | Alternatives | Native addon services |
| --- | --- | --- | --- | --- |
| 100 | 1 | 1 | 2 | 0 |
| 101 | 2 | 2 | 3 | 3 |
| 103 | 4 | 3 | 3 | 5 |
| 107 | 8 | 2 | 9 | 0 |

The witness driver selects quiet gateways using researcher truth, then must
legally discover, scan with its own source, exploit, escalate/inspect, deploy
empty-cache pivots and acquire native targets before a 300-tick deadline.
Native addon targets allow at most eight legal exploit attempts. Witnesses
establish reachable trajectories in these cells, **not autonomous reasoning,
universal solvability or a benchmark success rate**. No sessions are injected.

A fifth native witness composes depth-two service quarantine with Blue Restore.
Traffic—not an injected defender command—drives both responses. Restore removes
the pivot while its quarantine is active; its source cache disappears. The block
persists until release; legal reacquisition starts with an empty cache and can
complete the mission. This composes two implemented mechanisms; it does not
implement full host isolation, unisolation or patching.

The earlier native deadline check still demonstrates fast success at tick 16
versus quiet-route deadline failure at tick 18. That is a controlled software
example. Search's hand-counted deadline choices use its explicit estimate model.

Final checks: **149 Python tests**, **eleven frontend checks** and the production
build pass. `.local/observed-search-acceptance.xml` records zero failures, errors
or skips in the full Python suite. The pinned CC4
checkout remains unmodified.

## Preview and saved evidence

Latest service: `http://127.0.0.1:8796`, separate `.local/search-preview` data.
Earlier services are preserved. Paused initialized preview:
`0fb2556cc0e54113b05effe9021b03a0` at tick 0, no actions/model calls.
Import `configs/cc4-search-tradeoffs.json` for the new configurable example;
`configs/cc4-local-search.json` is the passive baseline example.

Saved software-only exploration fixture `7f0f77897ffa4bb5b05af9b53df5ab0b`
was copied from qualification evidence with its config, frames and fingerprints
preserved. It completes at tick 27, without overrides/model calls and with
`software_fixture=true`; this is one software case, not a performance estimate.
At tick 5, the UI shows its preferred exploit → inspect → pivot estimate.
Screenshots: `docs/screenshots/search-paused-workbench.jpg` and
`docs/screenshots/search-decision-plan.jpg`.

## Explicit remaining scope

This planner is a stronger deterministic control, **not** a globally optimal
joint multi-goal/team planner, a calibrated probabilistic/POMDP solver, or a
real-network validation. Unknown graph edges require exploration. Exploit and
escalation outcomes in continuations are optimistic and may fail. A search cap,
stale fact, shared retry exhaustion or bad frontier choice can prevent success.

The selected cells do not qualify every seed/population/service composition,
arbitrary topology or arbitrary deadlines. Autonomy with simultaneous native
Restore and quarantine is not claimed by the truth-guided composed witness.
No claim of research difficulty or mandatory LLM victory follows from success.

T12c wider service-change/contradiction composition, T12d broader technical
dependencies, T12e calibrated complexity profiles, T13a full isolate/patch
semantics, and T11 live-model qualification remain in the completion ledger.
These are open work with explicit scope boundaries; Phase 3 remains incomplete.
