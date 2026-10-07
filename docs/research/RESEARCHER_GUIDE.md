# Use the graduation workbench

On this laptop, open the running local demo at http://127.0.0.1:8797.
For a fresh research-only installation, use Python3.12 for CC4, Python3.12+ for
the service, Git and Node; this installation has service3.13.9/native3.12.5.
Native CC4 and legacy3.8 stay separate. No cloud, API key or model is needed for
scripted demos. From PowerShell at the repository:

```powershell
./tools/setup_research.ps1 -ServicePython python -CC4Python 'C:/path/to/python312.exe'
.venv/Scripts/python.exe -m backend.app.cli serve --port 8787
```

Setup builds software and installs dependencies; it runs no episodes/models.
The existing isolated CC4 checkout is pinned and must remain clean. Do not reset
local work to force setup. Research-only setup does not need the legacy simulator.

1. In Laboratory select **Graduation · investigative CC4**, a recipe, hierarchy/
   swarm/independent and1/2/4 workers (single worker independent). Choose common
   or matched split entry, conditions, evidence/communication delay, budget and
   mission hold/deadline. Recovery selects one shared Patch or native Restore.
2. **Initialize environment** saves/qualifies a new paused world at0. Settings do
   not modify a previous run. Unverified evaluation is excluded with inspectable
   tick-zero evidence. **Step** advances one joint tick; **Run/Pause/Stop** are
   explicit. Scripted means no LLM calls.
3. Switch researcher truth/private worker knowledge. Private graph edges are
   observed source/target/port probes; reported/stale does not mean current access.
   Inspect decisions, original/received evidence, native actions, messages,
   separate defense tracks/own symptoms and privileged mission hold.
4. Saved replay/export make no engine/model calls. Exploration allows manual
   eligible actions and records intervention; evaluation does not. Restarting the
   service retains evidence but starts no native checkpoint resume.
5. Experiment planner accepts an ExperimentSpec. Preview/preparation/export/save
   queue start nothing. Use configs/research-software-review-plan.json as an idle
   example. Recipes/custom dimensions beyond forms are JSON, validated identically
   through CLI and API; mechanisms/policies are code.
6. Review WORKED_MECHANISMS/ODD with your supervisor. Request separate scientific
   pilot execution authorization; after real pilot choose samples/variance/cost,
   then FREEZE_WORKFLOW and held-out tests. Never turn software checks into study
   results. The local queue has explicit limits and fresh technical retries only.

Local Ollama is optional. Choose the exact installed tag; the same private input,
candidate rules, organization and budgets apply. All leader/worker/repair tokens
count. A provider refusal/invalid/context/budget is an ordinary recorded outcome;
transport error/unknown cost is separate. The earlier Qwen check failed its first
request and is not successful live validation. Live scientific comparisons remain
outstanding. Long local integration checks must be bounded/background and saved;
they must not be repeatedly monitored in conversation.

Winning requires actual qualifying privileged target sessions for the full hold;
finding an address/token is insufficient. Complexity is adjustable but uncalibrated.
Programmed controls can win. The research question is how these concrete team
organizations affect investigation, dependency merging, adaptation and cost under
equal information/resources, not a guarantee that an LLM always wins.
