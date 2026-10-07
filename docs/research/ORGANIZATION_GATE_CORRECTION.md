# Delivered-task eligibility correction — 6 October 2026

This is a software fairness correction discovered during R6 calibration. Original
pilot outcomes and source snapshots remain immutable. It does not establish an
environment difficulty level or an LLM advantage.

## Evidence before implementation

Original delayed hierarchy run `847f00eb42f44d279700c6a1c9052b70` failed at179.
One instrumented native reproduction `83cd86cba4de4529b0184599ff83b944` used the
same config and unchanged controller/native code. It reproduced the terminal
failure with zero model calls. Wrapper observations at the actual decision point
recorded16 waits for no current assignment,28 mechanically unavailable tasks,
61 actions and211 waits for mechanically available, fully cited tasks excluded
by programmed strategy. Raw record: .local/organization-diagnostic-20261006/diagnosis.json.

Organization.preferred matched research assignments against Organization.options.
For scripted providers that list is strategy-filtered; for LLM providers it is
the mechanical catalog. Strategy preferences therefore became different assignment
admission rules between comparators. A leader can legitimately issue an older
task whose evidence has aged; age is not a missing owned prerequisite or proof
of hidden incompatibility. Admission must not infer whether it will succeed.

## Initial correction proposal and acceptance criteria

Use research mechanical candidates to revalidate an already delivered task for
every provider. Preserve the exact source/session/method/token and original
citations; all referenced evidence must still be locally visible. Missing owned
prerequisites or references must produce waiting, and an LLM worker must still
match its delivered task exactly. Do not rebind the task or acquire hidden facts.
Programmed ranking still chooses worker reports and leader tasks; its preferred
strategy is recorded, but it cannot redefine mechanical admission.

Record organization version1.1 and changed source identity for new episodes;
research strategy version1.0 stays unchanged. Existing pilot/source snapshots
remain versioned historical results and must not be pooled with new behavior.

Verification must include stale-but-visible task eligibility, forged citation and
wrong owned source rejection, equivalent scripted/mock-provider admission, and
an actual native episode through the corrected gate. Reproduce the old selected
config without changing horizon180/attempt12 or choosing new seeds. Report its
actual success/failure without requiring success as the acceptance condition.
Run the existing native organization/private-delivery and mock-coordinator checks.
No local Qwen call is needed to verify the admission correction; live integration
remains independently pending after its launch was rejected again.

Initial correction regression: existing native suite14 passed/1 failed; the
opposite-role delayed hierarchy missed its known working example. Keep that XML
and trajectory. Mechanical admission exposed obsolete instructions still issued
from reports preceding a worker's own completion. Add a provider-neutral report
clock stamped by the runner from an actually delivered actor report. A worker
waits on a task whose matching TRUE/FALSE completion it observed after that report;
a newer report permits deliberate re-investigation. This is generic task lifecycle
deduplication, not strategic filtering, hidden compatibility checking or a budget
increase. Preserve the original success assertion and rerun it plus relevant
native boundaries. This adjustment is declared before the next corrected outcome.

## Final decision: separate strategy from eligibility

The unconditional-follow proposal above and report-clock deduplication both failed
the existing opposite-role delayed-hierarchy success fixture. Their XML and
trajectories remain retained. The211 waits cannot establish that executing those
tasks would help: some represented legitimate programmed deferral of old tasks.
Do not label all211 as simulator/gateway rejections or a proven mission-failure cause.

Final organization1.1 separates two decisions. Organization.assigned uses the
mechanical catalog plus locally visible original citations. Organization.preferred
retains programmed ranking and may recommend Sleep. Run.advance binds a proposed
non-Sleep action to assigned, independently of that recommendation. Scripted
cognition still chooses its existing strategy; LLM/mock cognition chooses within
the same allowed delivered task. The report clock and forced-follow behavior are
removed. Source/session/method/token/citation identities and the hierarchy-only
assignment restriction remain intact. Mechanical availability does not force a
particular cognition strategy.

This resolves coupling of shared validation to cognition advice while preserving
programmed behavior. It does not claim that the original actual LLM path lacked
mechanical options: it already received them. The direct native test deliberately
returns an eligible delivered action when scripted advice is Sleep; the simulator
executes it successfully through the common gate. Worker/leader responses are
mocked, with healthy real transport and no live model. An initially unsupported
custom-link fixture was corrected to healthy transport; that setup error was not
a model/runtime or scenario-difficulty result.

## Verification evidence

- 16 unit strategy/gate checks pass: .local/organization-gate-separated-unit.xml.
- 7 focused gate checks including actual native execution pass:
  .local/organization-gate-actual-admission-final.xml.
- 15 existing native organization/private-delivery/mock-coordinator checks pass
  with unchanged success criteria: .local/organization-gate-separated-native.xml,
 196.77seconds. Includes the previously regressed delayed hierarchy.
- Archived attempts: .local/organization-gate-native.xml (14 pass/1 fail),
  .local/organization-gate-targeted-native.xml (1 fail); no outcome replacement.
- Initial forced-follow diagnostic run89c5a71b99f542cc87f5c5384f896b58 failed at179
  with1/2 targets,4 attempts; it is intermediate evidence, not the final patch.

Source fingerprints distinguish every version. Existing34 pilot episodes remain
historical, not pooled with organization1.1. These overlapping checks are software
evidence, not independent scientific trials. Gate correction accepted; research
calibration, expert review and successful local-model qualification remain open.
