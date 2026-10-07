# AbstractCyberSim research implementation package

**Current graduation implementation, 6 October 2026:** start with
[approved scope](APPROVED_SCOPE.md), [execution Goal](GRADUATION_EXECUTION_GOAL.md),
[requirement ledger](GRADUATION_REQUIREMENTS.md) and [checkpoint](GRADUATION_CHECKPOINT.md).
The revised plan governs scope and strict gate order. R0–R6 software gates are
accepted along with R7; all42 software items are audited in
[final acceptance](FINAL_ACCEPTANCE_AUDIT.md). Investigative mechanisms and both
organizations are implemented. Actual scientific/live/expert validation remains
separate. The original source audit and older figures below are historical.

[Researcher guide](RESEARCHER_GUIDE.md) · [Programmer handoff](PROGRAMMER_HANDOFF.md)
· [Presentation](GRADUATION_PRESENTATION.md) · [Worked native examples](WORKED_MECHANISMS.md)
· [Freeze/export workflow](FREEZE_WORKFLOW.md).

Prepared 3 October 2026. This package specifies the full proposed system. A first implementation now exists; see [current implementation status](../IMPLEMENTATION_STATUS.md) and the [root README](../../README.md) for delivered features and pending work. Research results do not exist yet.

The intended product is a local research workbench: configure LLM cyber teams,
inspect decisions and network effects, run controlled comparisons and export
evidence. The central comparison remains **hierarchy versus swarm LLM attacker
teams** under complex, partially observed, changing tasks. Rule/planner and
single-agent controls establish whether adaptation/coordination demands matter.

## Read in this order

1. [System design](SYSTEM_DESIGN.md): architecture, repository layout, agent semantics, simulator integration, UI, protocols, and configuration decisions.
2. [Research protocol](RESEARCH_PROTOCOL.md): questions, scenario suite, fair comparisons, metrics, analysis, validity, and publication requirements.
3. [Implementation plan](IMPLEMENTATION_PLAN.md): ordered engineering tasks with acceptance criteria.
4. [Configuration examples](examples/README.md): a hierarchy episode, a swarm episode, and an experiment sweep. They are design examples, not executable configurations for an existing runner.
5. [Contract definitions](CONTRACTS.md): implementation fields, invariants, and error categories for the process/API boundaries.
6. [Runtime audit](repo-audit.json) and [audit script](../../tools/audit_cyborg.py): evidence for the narrow multi-attacker compatibility fix and verified-address delivery bridge.
7. [Software validation plan](VALIDATION_PLAN.md): executable mission/organization acceptance fixtures, observed fixes, coverage and remaining limits.
8. [Phase 1–2 acceptance](PHASE_1_2_ACCEPTANCE.md): per-ticket closure, current test results, UI evidence and the Phase 3 boundary.
9. [Modular environment complexity](ENVIRONMENT_COMPLEXITY_DESIGN.md): renewed
   literature evidence, realistic behavior mechanisms, configurable modules,
   proposed contracts, UI/code split, qualification and revised build order.
10. [CC4 compatibility audit](CC4_COMPATIBILITY_AUDIT.md): inspected revision,
    nine bounded fixtures, isolated setup, native constraints and the decision to
    target a separate CC4 adapter before further legacy environment extensions.
11. [CC4 adapter acceptance](CC4_ADAPTER_ACCEPTANCE.md): delivered integration,
    software checks, setup, UI evidence and the remaining research boundary.
12. [Temporal complexity acceptance](TEMPORAL_COMPLEXITY_ACCEPTANCE.md): module
    controls, delayed/stale evidence, source/history, recovery, software checks
    and remaining T12 boundaries.
13. [Route complexity acceptance](ROUTE_COMPLEXITY_ACCEPTANCE.md): native source
    blocks, adjustable gateway layers/alternatives, hardened SSH accounts,
    explicit pivot deployment, private source selection and research boundaries.

14. [Mission complexity acceptance](MISSION_COMPLEXITY_ACCEPTANCE.md): sustained
    simultaneous access, live physical prerequisites, inclusive deadlines,
    native restoration/recovery, private projection and replay/export semantics.

15. [Baseline and diagnostic acceptance](BASELINE_DIAGNOSTICS_ACCEPTANCE.md): local
    rules, observed-frontier replanning, shared state facts, private choices,
    bounded development cells, exports and remaining research gates.

16. [Generated route tradeoffs](ROUTE_TRADEOFFS_ACCEPTANCE.md): seeded native
    service/time/privilege differences, private clues and traffic-triggered
    service quarantine; configurable synthetic assumptions and bounded evidence.
17. [Completion ledger](COMPLETION_LEDGER.md): explicit implemented/open
    requirements; explain proposed deferrals before advancing the plan.

## Main decisions

- Build the research application in the parent AbstractCyberSim repository, with CybORG as a pinned dependency and a small documented compatibility patch.
- Preserve hierarchy versus swarm as the primary comparison; use rule/planner,
  single-agent and independent controls to diagnose adaptation and coordination.
- Increase/decrease complexity through independently qualified module settings,
  with explicit behavioral assumptions and evidence; do not equate host count,
  randomness or use of an LLM with realism.
- Use a segmented enterprise network, independent red workers, and a separate cognitive coordinator for hierarchy. Each worker owns its own simulator sessions and memory.
- Expose ordinary research settings in the UI; persist the same configuration for a headless runner. New algorithms, action semantics, metrics, and scenario generators remain code extensions.
- Separate the physical network, the communication topology, and each agent's knowledge. Display all three.
- Keep the legacy simulator in its existing Python 3.8 environment; use a modern Python service and browser UI through a process boundary.
- Target CC4 for the complex research backend in a separate environment/adapter;
  the adapter is now selectable on Python 3.12 alongside legacy. [Software
  acceptance](CC4_ADAPTER_ACCEPTANCE.md) is established; scientific qualification
  and the full complexity program remain pending.
- Run the same core research loop from both the UI and command line. The UI never determines experimental results.

18. [Observed search and wider qualification](OBSERVED_SEARCH_ACCEPTANCE.md):
    bounded planning, shared historical connection facts, UI settings/plans,
    selected seed/population/service witnesses and native restoration during
    quarantine, with explicit remaining scope.

## Evidence and limits

Inspected local CybORG commit: `2742b5e0ce4330c9b14006b38acd3b5ebe00d6fd`. Runtime: Python 3.8.11, NumPy 1.21.6, Gym 0.23.1. The current README focuses on CAGE Challenge 3's drone scenario; enterprise templates and abstract cyber actions remain in the checkout.

The runtime audit creates enterprise teams of 1, 2, and 4 red workers. Stock port scanning fails with `KeyError('Red')`; changing two hard-coded session lookups to `self.agent`, temporarily in memory, allows discovery, scanning, exploitation, and independent session creation in those probes. This establishes feasibility for that path only. It does not establish correctness of every exploit, privilege escalation, defense, mission, reward, or proposed custom scenario.

A second probe confirms that a recipient's scan is invalid before receiving native knowledge of the address, becomes eligible after an allowlisted observed-interface update, and populates its own port cache only by scanning. The update grants no new sessions. This confirms the adapter hook, not a completed communication/provenance implementation.

No CybORG source file was changed during the original investigation. The subsequent implementation applies the documented two-line source patch. The older visualization under `CybORG/experiments` remains an exploratory drone demonstration with identical hierarchy/swarm rules; the new workbench is a separate offensive enterprise application. Neither is evidence of a completed research result.

## Source material

- User report: `C:/Users/sasok/Downloads/d.docx`, chapters 1, 4, and 5; hypotheses about swarm adaptability and hierarchical efficiency.
- User poster: `C:/Users/sasok/Downloads/Grad poster A1 (84.1 x 118.9 cm).pdf`.
- Original [AbstractCyberSim v-0.2](https://github.com/EviLooo/AbstractCyberSim/tree/v-0.2): rule-based cognition and organization placeholders.
- [CybORG source at the inspected revision](https://github.com/cage-challenge/CybORG/tree/2742b5e0ce4330c9b14006b38acd3b5ebe00d6fd).
- [CAGE Challenge 4](https://github.com/cage-challenge/cage-challenge-4): a separate enterprise multi-defender benchmark, not the checkout currently installed.
- [HPTSA](https://arxiv.org/abs/2406.01637): prior hierarchical offensive LLM teams.
- [Multi-Agent Collaboration in Incident Response](https://arxiv.org/abs/2412.00652): prior cyber-team organization comparisons in a tabletop setting.
- [Towards a Science of Scaling Agent Systems, version 3](https://arxiv.org/abs/2512.08296v3): controlled architecture comparisons and task-dependent effects.
- [AAMAS scope](https://cyprusconferences.org/aamas2026/call-for-papers-main-track/): agent coordination, evaluation, engineering, and simulation. This is venue-fit evidence, not a future submission deadline or acceptance prediction.

The proposed research question is a candidate contribution. A systematic literature update and empirical pilots must establish how it differs from prior work before any novelty claim is made.
