# Prepare a pilot without running one

In Experiment planner, paste a research ExperimentSpec, open “Pilot preparation”
and press “Prepare checklist without running”. Export the report. It includes
resolved jobs, team token and joint-tick ceilings, a loose request bound including
worker format repairs/leader calls, mechanism checks and failure recording.
Preparation constructs neither a simulator nor a provider and creates no runs.

CLI uses the same validated spec and preparation function:

```powershell
.venv/Scripts/python.exe -m backend.app.cli prepare-pilot configs/research-software-review-plan.json
```

These are upper bounds, not runtime/cost forecasts or a calibrated sample size.
Read WORKED_MECHANISMS with your supervisor; record criticism in REVIEW_WORKSHEET.
Check identical evidence boundaries, complementary merge and changed-evidence
recovery. Keep ordinary failure/refusal/invalid/context/budget separate from
technical errors, manual interventions and unknown model usage. Do not repeatedly
retry ordinary failure. Native witness failure is an unverified exclusion before
policy performance, not a mathematical impossibility claim.

An actual development pilot requires separate authorization. After that pilot,
use measured cost/variance/mechanism failures to choose bounded sample sizes and
predeclare endpoint/contrasts/exclusions/retry rules. Then freeze meaningful
development/validation/test combinations and exact policies/prompts/model hashes.
No scientific pilot, empirical difficulty or LLM superiority is claimed here.
