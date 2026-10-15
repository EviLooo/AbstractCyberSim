# Sequential queue: configuration first, explicit execution

Preview/save operations create no native worlds or provider requests. The UI
Experiment planner validates the same ExperimentSpec as the CLI and can save a
queue. Its execute control requires an explicit checkbox and job limit, and only
runs scripted decisions. Scientific execution remains outside the current task.

CLI (future researcher workflow, do not treat these as already executed studies):

```powershell
.venv/Scripts/python.exe -m backend.app.cli preview study-spec.json
.venv/Scripts/python.exe -m backend.app.cli batch-create study-spec.json
.venv/Scripts/python.exe -m backend.app.cli batch-run BATCH_ID
# The command above only reads status. Execution requires --execute.
.venv/Scripts/python.exe -m backend.app.cli batch-run BATCH_ID --execute --max-jobs 1
.venv/Scripts/python.exe -m backend.app.cli batch-stop BATCH_ID
```

Scheduling resume uses the execute command again. It creates a new recorded run
and attempt for an interrupted job; it never pretends to restore native state.
An OS lock prevents two executors of the same queue. Queue/state files live under
the configured data root's batches/BATCH_ID directory. Run evidence stays under
runs/RUN_ID. Stable attempt IDs bind batch, job and attempt index; different native
attempts retain different run IDs.

Default technical retries: zero. An explicit bound of zero to two may retry an
errored technical episode; ordinary mission/horizon/budget failure is never
retried. Unverified worlds are excluded before evaluation and are not retried
until a successful policy result appears. Every attempted episode remains in the
queue ledger. Stop requests are honored at native boundaries. Process-crash
recovery marks an old in-flight attempt interrupted and starts a fresh episode.

The CLI rejects non-scripted jobs before constructing a run unless a caller
explicitly enables live execution. The implementation task has not enabled or
tested that live path. Actual model validation and any costs require separate
authorization. Do not use an execution flag as a substitute for study approval.

Evidence: research-batches-acceptance.xml and
research-r5-recovery-queue-metrics.xml (bounded software fixtures, including one
real CC4 job). Queue completion means scheduling finished, not that every mission
succeeded. Scientific splits, frozen-policy checks and comparative exclusion
audits are still tracked separately in the requirement ledger.
