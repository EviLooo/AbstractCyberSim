# Supervisor / expert review worksheet

Prepared for later review; no reviewer has yet approved this model. One worked
trajectory per mechanism is required. Use the actual saved config/frame/decision
IDs, not a rewritten story or a successful trace chosen after a scientific sweep.

Reviewer, date, relevant experience, conflict/limitations: **pending**.

Four actual source-identified worked examples and checksummed full archives are
available in WORKED_MECHANISMS.md and examples/worked/. Preparation is complete;
reviewer feedback is still outstanding. Include failures within these trajectories
and distinguish A7 hold-reset proof from Restore before privileged hold begins.

| Mechanism | Evidence to inspect | Reviewer questions | Feedback / decision |
| --- | --- | --- | --- |
| Investigation | Identical-input native pairs in test_diagnostics.py and test_interfaces.py | Is the disclosed response sufficient to justify a different action? Does an unchanged retry fail for a plausible persistent prerequisite? | Pending |
| Dependency merge | test_credentials.py; complete hierarchy2/swarm4 test_interfaces.py traces; UI swarm2 demo t63 | Are bridge permission and account-reference possession distinct? Can only the owner originate the operation? Does coordination provide useful evidence without granting magical access? | Pending |
| Patch adaptation | test_changes.py and test_policy_recovery_native.py | Does the port remain visible while the old method ceases working? Does fresh contrary evidence reach the actor, rather than a hidden cause label? | Pending |
| Restore recovery | test_changes.py and test_policy_recovery_native.py | Do sessions/cache and hold really change? Is subsequent access reacquired through the same rules? | Pending |

For each trajectory record run ID, source/config/catalog versions, observation
IDs and their original/delivery times, action/source/method chosen, actual native
effect, communication, target state, and disputed assumption. Export the bundle.

Classify each comment: implementation defect / implausible abstraction / unclear
documentation / optional external realism test. Record the concrete requested
change and rationale, or the reason for retaining an assumption. Never recast
reviewer disagreement as approval. Changes after freeze require a new freeze.

Required report statement until review happens: "Mechanisms are specified and
software-qualified in bounded local fixtures; expert behavioral review remains
outstanding." No real-system testing is necessary to fill this worksheet.
