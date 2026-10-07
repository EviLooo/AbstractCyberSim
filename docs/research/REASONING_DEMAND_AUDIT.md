# Why the current software fixture is solvable without an LLM

5 October 2026. Read-only audit of implementation and saved software fixture
`7f0f77897ffa4bb5b05af9b53df5ab0b`. No additional runs or model calls.

## Finding

The 27-tick completion does not establish a demanding uncertainty/reasoning
scenario. Our implemented modules exercise native mechanics, but the accepted
fixtures do not yet demonstrate that information gathering, interpretation and
coordination are necessary to make good decisions. This is an open qualification
gap, not evidence that the full simulator is deterministic or every scenario easy.

## Actual run conditions and trajectory

The saved config selects one independent worker, one gateway layer, two
alternatives plus a dead end, one target, no addon services, passive native Blue,
disabled temporal evidence, no communication loss, a two-tick hold and deadline
150. Route-sensor detection probabilities are 1 for fast SSH and 0 for quiet FTP:
these endpoints deliberately remove sensor randomness in a causal software test.
The route sensor has one response, six-tick reaction delay and five-tick block.
The separate paused preview uses other settings; do not confuse it with this run.

Saved frames show discovery at t1, first scan t4, successful gateway exploit t6,
root/inspection t8, blocked/wrong-source target scans t9/t12, pivot completion
t11, service block t10–t15, successful pivot-source target scan t20, target
exploit t24, escalation t26 and mission completion t27. A dead-end exploit fails
at t18. The agent does not know the hidden release timer; its ordinary retry and
exploration behavior happens to outlast the short block. No route switch or
evidence-based diagnosis of the block's cause was necessary.

## Implementation causes

1. **Equivalent downstream routes.** `cc4/routes.py` assigns all gateways in a
   layer the same preceding source permissions and the same next-layer/target
   inventory. Templates vary duration, detection exposure and initial privilege;
   they do not create different technical dependencies or downstream routes.
2. **Direct next-hop leads.** Gateway `host.info` explicitly lists next-layer
   addresses. Native ExploreHost discloses that inventory after inspection. It
   does not reveal the full hidden ACL map, but following leads repeats the same
   scan → exploit → inspect → pivot workflow.
3. **Thin vulnerability decisions.** Generated SSH gateways mark a user
   bruteforceable, while the dead end uses strong accounts. Generated FTP uses
   FEMITTER; upstream FTPDirectoryTraversal's compatibility test returns True.
   Native reachability/service/session checks still apply. Generic
   ExploitRemoteService chooses its concrete exploit internally, so the agent
   does not infer and select a technique from version/configuration evidence.
4. **Forgiving change effects in this run.** Quarantine blocks service traffic
   but preserves sessions. Once its one budgeted response expires, that sensor
   cannot block again. Native Blue Restore was disabled; this is not sustained
   adversarial adaptation.
5. **Cheap mistakes and slack.** Failed scans/dead-end attempts consume time,
   but this run has 123 ticks remaining at victory, no expendable exploit/resource
   budget and no repeated access revocation. Retry/backoff suffices here.
6. **Much technical knowledge is already programmed.** Shared candidate logic
   encodes legal scan/exploit/escalation/pivot prerequisites, and local_search
   adds remembered facts and explicit action-chain planning. This is stronger
   than the original fixed-priority baseline; success should not be attributed
   to an LLM-style inference process.

## Required reasoning-demand gate before making the research claim

Retain strong non-LLM baselines. Build cases with observable evidence about
hidden service/configuration/dependency conditions; qualify that diagnostic
actions can change the preferred decision. Different routes must offer distinct
capabilities/prerequisites and consequences, beyond cost/risk template labels.
Ongoing observation-driven defenders and qualified service/patch changes must
invalidate earlier conclusions. Wrong actions must have meaningful declared
costs, while recoverable failures still have evidence-supported alternatives.
For organization comparisons, workers need complementary information/work
opportunities that cannot all be handled by a trivial common sequence.

Acceptance should include paired hidden-state cases with the same initial
observations, a legal distinguishing probe, and different justified subsequent
actions; blind retries must be measurably inferior under the fixed task budget.
Difficulty and calibration need later authorized pilots and held-out evaluation,
not software-test success counts. Use seeded reproducibility; do not replace
inferable uncertainty with arbitrary coin flips or designate an LLM winner.

These gates belong to unfinished T12b/c/d/e and relevant T13a mechanisms.
Explicit exploit-technique selection is currently optional T13b; if made central
to the hypothesis, promote its scope explicitly rather than imply it exists.
Deterministic problems can still demand planning, and uncertain problems can
still be solved by non-LLM methods. The unresolved issue is demonstrable decision
and adaptation demand in our chosen tasks, not determinism alone.
