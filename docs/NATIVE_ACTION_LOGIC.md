# How this workbench's cyber agents act

The enabled profile uses CybORG's native Scenario2 hosts, processes, services,
OS models, exploits, sessions and observations. The workbench adds teams,
organization, communication, cognition, controls and independent goal scoring.
No exploit runs against a real computer.

| Action | Native behavior and our gateway prerequisites |
| --- | --- |
| DiscoverRemoteSystems | Pingsweep of a known subnet, using the worker's active controller; returns observed addresses |
| DiscoverNetworkServices | Portscan of a known address; native reachability must allow it; successful service observations populate that worker's controller cache |
| ExploitRemoteService | Requires that worker's own scan cache. Native selector chooses a concrete modeled exploit from observed ports; the exploit checks modeled conditions and can fail. Successful access creates an actor-owned session, sometimes already privileged |
| PrivilegeEscalate | Requires a known hostname and active owned foothold. Native code selects a modeled escalation if needed, then ExploreHost reveals accessible host intel. It also inspects a host already at root/SYSTEM |
| Sleep | No worker operation. Native execution filters it out; its observation outcome is UNKNOWN |

For example, inspecting an owned User1/User2 reveals an Enterprise1 address in
the scenario's host information. Inspecting Enterprise2 reveals Op_Server0's
address. An already privileged foothold can still need this inspection before
the agent knows where to go next.

The goal requires active root/SYSTEM sessions on every configured target,
counted once across the team. Observing a target or merely issuing an exploit
does not satisfy it. Researcher truth is available for inspection; policies
receive their own observations and delivered reports only.

Hierarchy workers wait for delivered coordinator assignments. Swarm workers
select from their own eligible actions and react to delivered peer claims.
Addresses can be shared through engine-verified evidence; scan caches and
sessions remain private. Communication delay/loss is a separate organizational
model, independent of the native physical graph.

This legacy scenario includes an inherited rule requiring an Enterprise-named
session owned by the acting worker before contacting Operational addresses.
It is a simplified permission rule, not a general firewall implementation.
Monitor observes activity; the enabled defender never removes/restores access.
Full recovery and generic network rules need separate qualification.

Source: `packages/engine_worker/runtime.py`, `backend/app/policies.py`, and native
`CybORG/CybORG/Simulator/Actions/AbstractActions/`, `Actions/Action.py`, and
`Scenarios/scenario_files/Scenario2.yaml`. Tested coverage and remaining limits
are specified in [the validation plan](research/VALIDATION_PLAN.md).
