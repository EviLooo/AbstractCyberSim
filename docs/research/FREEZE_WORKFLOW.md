# Freeze, run and reproduce a study

Freezing starts no competing actions or model calls. First initialize each exact
materialized configuration to save a legal native witness; unverified cases are
excluded before any policy outcome. Keep technical errors distinct from scientific
failures. A witness does not supply agent knowledge or prove behavioral realism.

Declare existing qualified run IDs in `worlds`, assigning development/validation/
test. The freeze rejects the same causal configuration across splits, even when
IPs/opaque identifiers differ. Test combines previously represented recipe,
condition, entry and change components/role placements. For example development
can cover enabled+placementA and disabled+placementB; validation enabled+B; test
withholds disabled+A. This holds out a combination, not an undocumented technique.

`cognitions` explicitly adds allowed policy/model settings. `episode_treatments`
adds explicitly allowed public transport/claim/tool-capacity configurations whose
materialized world is already qualified. Architecture and recorded replicate
seeds are treatment/run metadata; other transport/action-cap settings cannot be
silently changed after freeze. Every queued world and native world hash is checked.

`purpose: software_qualification` never contributes scientific estimates.
`purpose: proposed_study` requires primary_endpoint, contrasts, exclusions,
retry_rule, sample_size_rationale and development_pilot_reference. Actual pilot
authorization/results cannot be replaced with a fictional reference. Tools validate
the fields; a researcher must ensure the reference and scientific choices are real.

For Ollama treatments, `model_artifacts` maps the exact model tag to its installed
manifest file under `models/manifests`. The freeze hashes the manifest and all
referenced local content-addressed blobs. It rejects arbitrary marker files.
Before an explicitly authorized frozen live queue, the local `/api/tags` metadata
must match that manifest hash. This metadata check performs no generation. Keep
the model store unchanged during execution; preflight is not an atomic lock on
Ollama's separate process. Weights are identified, not copied into the ZIP.
([Ollama API](https://github.com/ollama/ollama/blob/main/docs/api.md))

Freeze saves exact source snapshots, source/catalog/prompts/engine/dependency
hashes, Python runtime, resolved worlds, qualifications and model artifacts.
Source/settings/model changes require a new freeze. Preserve old evidence; do not
edit baselines after inspecting test results. Compare one frozen split at a time.

```powershell
.venv/Scripts/python.exe -m backend.app.cli study-freeze my-split-manifest.json
.venv/Scripts/python.exe -m backend.app.cli study-check STUDY_ID
.venv/Scripts/python.exe -m backend.app.cli batch-create my-plan.json --freeze STUDY_ID --split test
# Execution requires separate authorization; this command alone prints saved status:
.venv/Scripts/python.exe -m backend.app.cli batch-run BATCH_ID
.venv/Scripts/python.exe -m backend.app.cli study-export STUDY_ID .local/study.zip
```

The UI provides the same freeze JSON, saved queue binding and ZIP export. A ZIP
contains frozen source, full bound run evidence, CSV, analysis and PNG/SVG figures,
with checksums and reproduction notes. Technical/interrupted/unverified/manual/
unknown-cost outcomes remain counted/excluded appropriately. Formula versions
cannot mix. Failures retain their horizon time; repeated observations cluster by
causal world. One world has no confidence interval. Software-only archives show
“no eligible study observations”, never an invented estimate.

After source changes, export archives evidence but omits new-code analysis.
Reproduce with the bundled frozen source/runtime/dependencies and content-identified
CC4/model artifacts. Old freezes without source snapshots explicitly report them
missing. Replay/recompute constructs no simulator/provider and preserves input.
Study estimates remain descriptive; small bootstrap samples do not prove novelty,
real-world transfer, significance or an LLM/organization advantage.
