# Research metrics v1.1 (software qualification)

Implementation: backend/app/research_metrics.py. Historical formula 1.0 is
preserved; research frames additionally emit research_metrics_v1.1. Offline use:

```powershell
$env:RESEARCH_DATA_DIR='C:/Users/sasok/Documents/ChatGPT/AbstractCyberSim/.local/graduation-demo'
.venv/Scripts/python.exe -m backend.app.cli recompute RUN_ID --output .local/recomputed.json
```

This reads saved configuration, frames and usage only. It neither starts an
engine nor contacts a model, and does not rewrite historical run evidence.

Access admissions count valid submitted AttemptAccess once. Completed attempts
count native completion, including continuations. Their difference is partial
work, not success or refunded budget. Probe/inspection counts use valid completed
actions. Native ticks are joint ticks, not workers multiplied by ticks.

Restricted completion uses the first success tick, or the declared horizon for
an unsuccessful episode. Only eligible terminal evaluation episodes may enter
a study estimate; an interrupted/technical/exploration episode is not an ordinary
horizon failure. Success and censoring remain explicit.

An unchanged repeat has the same actor, source, target, method and token, within
the same own-access epoch, with no new cited probe/artifact evidence. This is a
conservative behavioral flag, not proof that any repetition is irrational.
Failed-action result IDs alone are not new compatibility evidence. A fresh probe
may justify a repeat even if its response happens to be unchanged.

Comparable simultaneous admissions match public action/target/source/method/
probe/port/token; differing evidence IDs do not hide duplicate work. Distinct
sources are different investigations. Sleep counts are worker wait ticks,
including voluntary idle choices, not automatically organizational failures.

Transport costs count every recipient-copy envelope and its UTF-8 bytes, with
created and delivered amounts separate. Assignment/report/claim counts are copies.
Evidence age is joint tick minus original observation tick for citations in an
admitted action. Relaying a record cannot rejuvenate it. Age is not correctness.

Recovery starts from an actor's recorded own-session loss. Report first subsequent
valid completed action as renewed progress, and actual recorded same-host session
recovery separately. No recovery is censored. No observed loss has no recovery
latency, rather than latency zero. A separate changed-compatibility reducer starts
when a newer service response contradicts an earlier positive response upon actual
delivery. It records the first subsequent valid completed same-address access and
its method/source, with censoring when absent. Late old relays cannot replace newer
observations. This detects observed behavior, not an oracle attribution to Patch.

Model usage includes every worker, leader and repair call. Unknown costs remain
conservatively charged reservations, including cancellation while a request is
in flight. Per-actor totals distinguish leader cost. Live-provider validation
remains outstanding; mocked integration is not a scientific comparison.

Hand-counted evidence: research-metrics-unit.xml and
research-provider-cancellation-metrics.xml. Actual saved demo recomputation:
.local/graduation-demo-metrics-recomputed.json. The latter is a bounded software
demo, not a scientific result. Full outcome, patch-recovery and comparative
qualification remain open in the requirement ledger.

Version1.1 corrects renewed progress to valid completed actions, and adds unique observed conflicting field records, contradicting field refreshes, stale citations at admission and admitted same-target method/source changes. Conflict/refresh fields describe the recipient ledger (including native session changes), not a truth-level change count or successful reasoning. Old saved v1 metrics remain immutable; recomputation explicitly reports v1.1. Native Restore hand count under the current qualified controller: access9, loss11, renewed inspection13, restored18, privilege20, final3-tick hold at22; earlier UI replay24 retains its earlier controller source.
