# Segmented route complexity checkpoint

Later extension, 5 October: [generated route tradeoffs](ROUTE_TRADEOFFS_ACCEPTANCE.md)
adds service/privilege diversity, native exploit durations, private scan clues
and bounded service ACL quarantine. Alternatives now support 1–9 with population
validation. The original two-way SSH acceptance below remains historical scope.

4 October 2026. Delivers the first bounded T12b profile on the accepted CC4
adapter. It adds actual source-dependent service access, alternative gateways,
native account incompatibility and an explicit pivot deployment extension.
This is software qualification, not an empirical realism or LLM superiority claim.

## Configuration and execution

Use `configs/cc4-routes.json`, or select CC4 and the **Segmented routes and
alternatives** development preset under **Environment complexity**. Initialize
starts paused. Changing a setting creates a new world; it does not mutate an
existing episode. Scripted mode makes no model calls.

`scenario.complexity.routes` is an additive schema-1.0 module:

| Setting | Range | Effect |
| --- | --- | --- |
| `enabled` | boolean, default false | Keep the native profile or apply segmented host-source rules. |
| `depth` | 1–3, default 1 | Number of gateway layers before the named targets. |
| `alternatives` | 1–2, default 2 | Independently reachable gateways per layer. |
| `hardened_dead_end` | boolean, default false | One additional reachable SSH host per layer with no brute-forceable account. |

Native CC4 users/servers/add-on services remain separately adjustable. Gateway
hosts use an SSH-only template. Targets retain their native generated services
and the native abstract exploit selector. The contractor server cannot be a
mission target when used as the hardened dead end; validation rejects this.

The route recipe uses existing native hosts and router edges. It does not draw
a replacement physical graph. A separate deterministic stream
`random.Random("routes:1.0:<world_seed>")` chooses gateway order and later zones.
Each target or next-layer gateway accepts service actions only from an allowed
previous-layer host. All other source hosts, including arbitrary acquired
intermediaries, are blocked by native `state.blocks` entries. Native
`DiscoverNetworkServices` and `ExploitRemoteService` enforce these entries.
ICMP host discovery remains allowed; discovering an address grants no service
access. The native mission-phase policy remains distinct from actual ACLs.

After gaining privilege, native `ExploreHost` reveals configured inventory
addresses for the next layer. Inventory provides no ACL, vulnerability labels
or winning-route instructions. Workers see only their observed/delivered
addresses, own sessions, own source-specific caches and native action outcomes.
The full recipe belongs exclusively to researcher truth and saved world inputs.

## Explicit extension: EstablishPivot

Stock CC4 exploitation creates ordinary shells, not additional scan controllers.
`EstablishPivot` is **our extension**, registered only when routes are enabled.
The action takes two joint ticks and rechecks at execution that the issuing
controller and privileged, non-sandbox target shell are active and actor-owned.
It converts that existing shell to a native `RedAbstractSession`, preserving
its session ID, PID, parent, children, ownership and privilege. It initializes
empty port/OS caches. It creates no new access, bypasses no firewall, shares no
teammate capability and makes no implicit pivot after exploitation.

Subsequent scans/exploits originate at the selected pivot's hostname. Service
cache admission is specific to that source. Native Restore removes the pivot
through its existing session/process effects. Acquiring another gateway may
provide another source; regaining the removed gateway requires exploitation,
privilege escalation and explicit deployment again. Removing an upstream source
does not imply every independently established downstream controller must die;
native session semantics decide the effect. This is not a full tunnel/C2 model.

## Repository boundaries and visualization

- `packages/contracts/complexity.py` defines strict controls; registry and
  generated schemas/types support API validation, import/export and presets.
- `packages/engine_worker/cc4/routes.py` materializes templates/inventory/ACLs
  and implements deployment. `scenario.py` registers it; `runtime.py` installs
  blocks at creation and records actual controller changes and world inputs.
- `backend/app/policies.py` considers every owned controller without consuming
  physical truth. Completion/retry keys include nonzero source IDs. Hierarchy
  preserves a worker's proposed source; sessions cannot be delegated. Private
  scan timestamps distinguish sources. Observable loss permits replanning.
- UI controls expose the four knobs and saved settings. The researcher route
  flow shows permitted source dependencies separately from physical cables,
  active worker controllers, dead ends and materialized rules. The private view
  shows only that worker's controllers. Manual actions include an owned-source
  selector; attempted source IDs and controller changes are saved for replay.

Initial `world.json` includes the exact native hosts, interfaces, services,
users, ACLs and route recipe. Every frame retains actual blocks and the recipe.
The module manifest resolves settings and hashes independently of architecture.
Identical worker count/settings/seeds materialize identical hierarchy/swarm
worlds. Disabling routes matches an omitted module under this code revision.
Earlier serialized world formats are historical; code fingerprints distinguish
comparisons across revisions.

## Software checks

The complete regression passed **92 Python tests** (144.77 seconds), including
the earlier 80 checks and twelve added route checks. The JUnit result is
recorded in `.local/routes-acceptance.xml`. Seven frontend checks and the
production build pass. CC4's pinned checkout remains unmodified.
`tests/test_cc4_routes.py` adds twelve bounded checks:

- strict limits and conflicting target rejection;
- complete legal native trajectories for 1/2/4/8 workers, depth 1/2/3 and one/two
  alternatives, including failed direct scans and failed hardened SSH exploitation;
- no deployment before privilege, empty new caches, unchanged private boundaries;
- reset reproducibility, architecture pairing, seed changes to actual rules and
  blocks, and disabled-module equivalence;
- source-specific candidates and retained hierarchy controller assignments;
- isolated native adversarial fixture: even an injected old scan cache cannot
  bypass stock exploitation's firewall check; teammate sources are rejected;
  five-tick native Restore removes a monitored second-layer pivot, the alternate
  still scans successfully, and reacquisition produces a fresh empty cache;
- bounded hierarchy/swarm/independent pipeline missions using private data,
  source-specific scans and deployment, zero model calls, with saved replay;
- source-specific evidence ages and retries after own observed access loss.

Fixture missions use passive defense and SSH-only targets to isolate dependency
semantics. Organizational fixtures use a one-layer, two-worker profile without
dead ends and age threshold 1000. These are technical fixtures, not a benchmark
ranking. The restore probe deliberately schedules one native Blue action on a
covered host; existing CC4 adapter tests separately qualify the fresh-sensor
reactive policy. The full space of population, defense, age, route depth and
communication combinations is not qualified by these samples.

Seven frontend logic checks include private route projection. Browser checks
cover the development preset, route controls, initialization at tick 0,
researcher versus worker views, source selection and saved route visualization.
No experiments or live model calls were launched.

Visual evidence: [initialized two-layer environment](../screenshots/routes-initialized-workbench.png)
and [saved successful software-fixture replay](../screenshots/routes-mission-software-replay.png).
The replay fixture ends with privileged target access; deployment on a mission
target is optional, so a target can have a privileged shell without a controller.

## Behavioral grounding and remaining limits

Source allowlists and jump-server restrictions are documented in
[CISA AA25-239A](https://www.cisa.gov/news-events/cybersecurity-advisories/aa25-239a).
Using acquired internal hosts to relay activity is documented by
[MITRE Internal Proxy](https://attack.mitre.org/techniques/T1090/001/), and remote
service access by [MITRE T1021](https://attack.mitre.org/techniques/T1021/).
These sources ground mechanisms. They do **not** validate this generated
topology, weak-account fraction, privilege requirement or two-tick deployment
duration. Those are declared synthetic modeling assumptions.

CC4 has no native Blue coverage in the contractor subnet: the first layer is
outside monitoring. Later generated layers are in native Blue territories.
No dynamic ACL changes, patching, host isolation, packet protocols, realistic
credential stores, C2 fidelity, arbitrary graph generator or CVE calibration is
delivered here. Native Linux privilege escalation is a broad OS eligibility
abstraction. Service vulnerabilities are modeled as native templates, not actual
software exploits. Abstract exploitation still chooses the concrete technique.
The existing `duplicate_actions` metric counts concurrent equal action/target
attempts; different necessary sources can contribute, so it is not a waste metric.
Finer coordination/route-efficiency metrics remain T12f work.

T12b's first bounded profile is implemented. T12d sustained/multiple-objective
missions and deadlines are next; T12f diagnostics and live LLM qualification,
behavioral validation and frozen research evaluation remain separate milestones.
No setting is tuned to guarantee an LLM or an organization wins.
