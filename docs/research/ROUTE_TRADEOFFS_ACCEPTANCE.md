# Generated route tradeoffs

5 October 2026. Delivers the concrete missing T12b route-tradeoff extension:
native service/privilege diversity, configurable exploit times, private scan
clues and bounded traffic-triggered service quarantine. This does not close
every T12b requirement or qualify a research difficulty ladder.

## Configuration and native effects

`configs/cc4-tradeoffs.json` initializes paused: one independent worker, two
targets, one gateway layer, two alternatives, one hardened dead end, hold 5,
deadline 180, horizon 240. Native Blue is passive; the separate route sensor is
active. No automatic Step, Run, experiment or model call occurs.

Controls are at `scenario.complexity.routes.tradeoffs`. Old configs default to
disabled. Routes allow 1–9 alternatives, bounded by `cc4.user_hosts - 1`.
Tradeoffs require at least two; optional privileged access requires three.
Depth remains 1–3. These are existing native enterprise hosts/source ACLs, not
an arbitrary graph or arbitrary count of enterprise zones.

| Template | Real simulated service/session effect | Default exploit ticks | Separate sensor probability |
| --- | --- | --- | --- |
| `fast_ssh` | SSH-only weak user account; native SSHBruteForce creates user access | 2 | 0.9 |
| `quiet_ftp` | FEMITTER FTP process running as user; native FTPDirectoryTraversal creates user access | 8 | 0.1 |
| `privileged_ftp` (optional) | FTP running as root; native exploitation creates root access directly | 6 | 0.4 |

Each layer contains fast and quiet variants, plus privileged when selected.
Extra gateways repeat this template set. Assignments are shuffled with the
separate `route-templates:1.0:<seed>` stream; native population randomness is
unchanged by assignment. Adjacent seeds can repeat a small permutation.
Same settings/seeds/worker counts match across hierarchy and swarm.

All durations, probabilities and response controls are editable, with strict
bounds. Quiet must take longer and expose less to the route sensor than fast.
FTP reuses an already reserved process PID and creates a native process/service;
native exploitation creates the actual actor-owned session. Gateway exploit
duration uses CybORG's normal busy/continuation clock. Owned controller, observed
target, own source scan cache and native firewall checks remain required.

These are synthetic controls, not measured CVE costs or exploit success odds.
Native FTPDirectoryTraversal's compatibility check is broad (`True`): no patched
FTP/version fidelity is claimed. Hardened SSH still fails through the native
account prerequisite. The abstract exploit action still chooses the concrete
technique. No fabricated credential model or UI-only access grant exists.

## Private evidence

A successful own service scan discloses a limited `Route clue`: service,
estimated exploit duration, high/medium/low route-sensor exposure and an ordinary
versus privileged service-account hint. This is a declared synthetic assessment,
not a claim that stock CC4 port scans expose exact service configuration.
It reveals no precise probability, ACL, downstream route or guaranteed success.

Normal observation delay applies. Verified forwarding requires sender-owned
evidence and actual delivery; a recipient gains no native source cache or access.
All providers see the same allowed memory. Local policy version 1.1 uses observed
exploit-time estimates and records clues; existing priorities/frontier heuristics
otherwise stay unchanged. It is not a risk-optimal route planner.

## Sensor and service quarantine

`RoutePressure` is our explicit extension, separate from native Blue Monitor.
It covers generated gateways, including the first contractor layer that native
Blue cannot monitor. Each completed reachable scan/exploit samples its declared
probability with `route-sensors:1.0:<seed>`. Inputs are traffic metadata, not
compromise/session inventory or exploit success. Rejected, busy, dropped and
currently blocked attempts create no new route-sensor event. Probability is
per completed operation, not per tick or whole mission.

Alerts occur after native execution. A response applies before native tick
`signal_tick + reaction_delay`, lasts `block_ticks` execution ticks and releases
before its recorded release tick. The route response budget is global and
separate from native Blue's per-agent Restore budgets. Turning responses off
records alerts without altering access.

The response adds native `state.blocks` entries for traffic into and out of a
gateway. Native scans/exploits enforce them, including an already pending exploit.
Release removes only this module's additions, preserving existing unrelated
blocks. Sessions, privilege, ICMP discovery and local inspection/deployment remain.
This is service ACL quarantine, not full host isolation, C2 teardown or patching.
The current composition has no second host-ACL writer; future writers require an
explicit shared lease/ownership contract before combined qualification.

Native monitoring/restoration remains separately selectable. Low route-sensor
exposure does not suppress native SSH/FTP events or guarantee low total detection.
Workers cannot see alerts, global block state or exact release times. They observe
action failures and their own session status. Mission scoring still checks actual
privileged access: a traffic block alone does not revoke already held access.

## UI and persistence

**Environment complexity → Fast exposed / slower quiet routes** exposes the
module controls; mission deadlines remain in the mission editor. UI, JSON and
API share the strict contract. The researcher route table shows generated
services, times, privileges, sensor probabilities and current blocks. Worker
views show only own/delivered clues and owned controllers.

Frames retain native durations/outcomes, traffic observations, alerts and
block starts/releases. Truth includes `route_pressure`; cognitive inputs do not.
The existing defender event panel and JSON/ZIP exports preserve this evidence.

## Acceptance

**129 Python tests, ten frontend checks and the production build pass.**
`.local/route-tradeoffs-acceptance.xml` records zero failures/errors/skips.
The pinned CC4 checkout remains unmodified.

Thirteen new cases in `tests/test_route_tradeoffs.py` verify strict controls and
population bounds, architecture-independent compiler output, deterministic
sensor timing/budget and ACL preservation, delayed clues and observed policy
costs, API validation, 2/3/9-alternative native service generation, SSH/FTP outcomes
and actual privileges, own-cache/forwarding boundaries, native durations/busy
admission, sensor-triggered exploit denial/release, surviving pivots with denied
outgoing traffic, and a four-worker mission across two mixed-template layers.

A controlled one-target fixture with deadline 18 wins at tick 16 through fast
SSH and misses the deadline through slower FTP. This isolates implementation of
time tradeoffs using manually specified legal actions. It is not an autonomous
baseline comparison or research experiment. Probability extremes 0/1 isolate
sensor effects; default rates are not calibrated by these fixtures.

Browser checks verify preset selection, duration/population validation, clean
module disabling, readable generated tables and private views retaining observed
clues while hiding exact probabilities and block release times. The copied
manual software fixture `34dd018a756c458e978e6ff2c8b69b44` finishes at tick 21,
with zero model calls. It carries `software_fixture=true`, exploration purpose
and manual intervention, so it cannot enter scientific comparisons. Its tick 9
frame shows the failed native scan through a still-owned but quarantined pivot;
the block expires at tick 13. Saved-run acceptance checks these artifacts.

The new preview is at port 8795. Run `8fec545650f144969dc2430a05ff052b` remains
**ready at tick 0**; no Step or Run was issued. It uses the default two-target
tradeoff config above. Earlier services and runs remain intact.
[Initialized route table](../screenshots/tradeoffs-initialized-workbench.png).
[Saved block and observed clues](../screenshots/tradeoffs-block-and-clues.png).

## Open work

Credential discovery/use/re-entry remains T13b: a credential route needs an
actual native mechanism. Explicit technique selection, patches, full host
isolation and generic graphs remain unimplemented. Their optional/conditional
placement is unchanged, and service quarantine does not substitute for them.

Broad seed/population/composition qualification, stronger observed-information
planning baselines, live model qualification, behavioral calibration and
authorized pilot/final evaluations remain open in the completion ledger. No
LLM necessity/superiority or empirically validated realism is claimed.
