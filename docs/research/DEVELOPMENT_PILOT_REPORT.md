# R6 developmental calibration report — 6 October 2026

The selected programmed controllers completed31 of34 episodes across two recorded
development iterations. Three organization cases exhausted the native horizon.
No episode had a technical error, exclusion, retry or model call. This pilot exposes
remaining calibration gaps; it does not establish LLM superiority or real-world fidelity.

## Provenance and scope

Initial23 freeze: `89debcb0d0c1e3ea46d8e22f22f42aa964ecfc07f4fb1aa60d6893d24dd4a15a`;
batch `cb16985c0d0972248fd7ace19d47c167`.
Follow-up11 freeze: `a1146f3ba67a29cf2ebf45f4650a0f423b34fbfcf69662768aef05254e466f12`;
batch `20cb5b06ac955286e720c5c106f8f6dc`.

Each iteration saved exact validated configs and source before execution. The
follow-up was preselected after examining the initial results and is explicitly
developmental. The driver changed; four controller files remain byte-identical
across both snapshots and the working tree at the initial audit. All original
outcomes remain intact. Subsequent organization1.1 gate correction changes the
current source identity: these pilot results are now historical/archive-only;
see ORGANIZATION_GATE_CORRECTION.md. They must not be mixed with corrected episodes.
Both use horizon180 native steps,12 shared access attempts and zero scripted model
calls. End tick179 means the indexed native horizon, not a shorter declared budget.

Raw runs, frames, events, qualification, CSV and source snapshots are under
`.local/development-pilot-20261006` and `.local/development-pilot-artifacts-20261006`.
The portable compact evidence index is [examples/development-pilot-20261006.json](examples/development-pilot-20261006.json).
An offline audit checked all34 witnesses, zero calls, terminal native success/ticks
against recorded metrics and saved metadata/final-frame hashes.

## Investigation: effort changes, success still easy

Each table cell is one successful episode. Parentheses contain admitted access
attempts. All are one independent worker; policy source stayed fixed at version1.0.

| Configuration | Fixed workflow | Evidence controller | Observed planner |
| --- | --- | --- | --- |
| Linear control, valid cached key |11 (1)|11 (1)|14 (1)|
| Import enabled, valid cached key |11 (1)|11 (1)|14 (1)|
| Import disabled, valid cached key |19 (3)|11 (1)|14 (1)|
| Import disabled, invalid cached key |19 (3)|15 (2)|18 (2)|
| Import enabled, wrong-scope cached key |11 (1)|11 (1)|14 (1)|
| Denied initial source, invalid cached key |57 (5)|64 (4)|59 (3)|

The fixed workflow used zero probes. Evidence and planner controllers used one/two
probes in the initial cases, and respectively5/4 in the denied-source follow-up.
The valid cached key provided an alternative credential route, so changing import
compatibility alone did not require finding a new token. Wrong-scope key plus
enabled import retained an easy compatible alternative. Denied source required
more exploration, local inspections and source changes, but every controller
still completed. There is no demonstrated requirement for an LLM in these cells.

## Organization: some real failures, communication not compulsory

These are the evidence controller with the same declared horizon/attempt budget.

| Workers / transport delay | Independent | Hierarchy | Swarm |
| --- | --- | --- | --- |
|2 /0|Success93|Success151|Horizon failure179|
|2 /2|Success93|Horizon failure179|Success84|
|4 /0|Not selected|Success87|Horizon failure179|

Two independent workers could acquire their own capabilities without messages.
Identical independent outcomes at both transport delays are expected; transport
does not affect a team that exchanges no messages. Do not count those as extra
independent network evidence. Coordination can help or hinder, but the current
dependency fixture does not make exchanging capabilities compulsory.

The delayed hierarchy failure is actual run `847f00eb42f44d279700c6a1c9052b70`:
zero of two privileged targets at179,2 admitted attempts,653 delivered messages.
Native final actions were Sleep while delivered reports still contained possible
access/probe candidates. This is an observed coordination stall; it has not been
proven to be caused by a particular assignment bug. Keep the outcome and trace,
and diagnose separately before deciding whether a software defect requires a new
controller version and a new development freeze. Do not silently repair/retry it.

Actual local UI replay was checked on8798: the completed native record, zero
tokens, missing targets, stale evidence and organization graph are visible.
Screenshot: [hierarchy replay](../screenshots/development-pilot-hierarchy-failure.jpg).
The replay does not advance the simulator. The prior user demo on8797 is preserved.

## Defender response: execution is not necessarily a recovery treatment

| Selected condition | Hierarchy2 | Swarm2 |
| --- | --- | --- |
| Patch response2 |Success26|Success20|
| Patch response8 |Success29|Success21|
| Restore response4 |Success26; no observable loss|Success20; no observable loss|
| Restore response8 |Success26; no observable loss|Success28; one observable loss|

Restore4 took effect before access in both organizations, so neither episode
tested recovery. Later Restore8 caused Red_0's loss at17 in swarm run
`2140e64a659443088dacf4debfce8402`. Native records show Restore and own session
loss at17 while privilege escalation was in progress; it completed FALSE at18.
Renewed exploratory progress
appeared three ticks later; Red_0 did not regain that host by mission completion
(recovery latency is censored, not zero). Red_1 retained/gained target access and
the team completed its three-tick hold at28. The hierarchy pair had no loss.
This demonstrates team redundancy under one loss, not matched recovery quality.

## Required next gates

1. Qualify a single local Qwen worker through the actual private/native interface.
   This separate bounded integration checks structured decisions and accounting;
   it supplies no architecture ranking. Previous local request failed at tick0.
   Keep failures and return after background launch as the user requested.
2. Finish development calibration before a final team study. Use supported
   combinations that require fresh evidence and several prerequisites; declare
   those configurations and criteria before outcomes. Include simple controls.
   For recovery contrasts, distinguish observable loss, successful avoidance and
   a defender acting before access. A response label alone is not a treatment.
3. Investigate the preserved organization stalls. If a genuine implementation bug
   exists, document the fix, new policy/source identity and fresh development
   checks; keep previous results as historical. Do not weaken the baseline.
4. Obtain external behavioral review using REVIEW_WORKSHEET and these trajectories.
   No supervisor/expert feedback has been supplied or invented.
5. Predeclare sample rationale, contrasts, exclusions, budgets and retries, then
   freeze new held-out combinations for R7. A final scientific sweep and live team
   comparison are not run or claimed here.

One observation per selected cell, shared placements/rules and post-initial
development follow-up cannot establish significance, network generalization,
realistic difficulty or that an LLM must win. Software delivery remains complete;
research calibration, live validation and the paper remain unfinished.

Local Qwen launch status: automatic approval review rejected the attempted bounded
background launch before execution, with the sole reported reason "blocked by
policy". No new process/model call/result exists. Prepared config, installed
manifest/blob hashes and runtime decision remain in .local/qwen-integration-20261006;
launch-rejection.json records the exact limit. This is not a provider/model error
and no particular safeguard cause is inferred. Successful live qualification is
still outstanding.

Subsequent work: the user-authorized launch retry was also rejected before
execution (launch-rejection-retry.json). No model request or retry result exists.
The preserved hierarchy stall was reproduced with unchanged source, then the
shared assignment validator was separated from cognition recommendation under
organization1.1. Forced-follow/report-clock attempts failed existing acceptance
and were rejected; final native15, unit16 and focused gate7 pass. Programmed
strategy remains unchanged and its original failures remain valid developmental
observations. See ORGANIZATION_GATE_CORRECTION; do not claim the strategy's211
deferred decisions were all illegal actions or proven bugs causing the failure.
