# AbstractCyberSim research implementation package

Prepared 3 October 2026. This package specifies the full proposed system. A first implementation now exists; see [current implementation status](../IMPLEMENTATION_STATUS.md) and the [root README](../../README.md) for delivered features and pending work. Research results do not exist yet.

The intended product is a local research workbench: configure LLM cyber teams, inspect their decisions and network effects, run controlled comparisons, and export reproducible evidence. The paper remains about agent-based modeling and organizational effects on simulated offensive cyber operations.

## Read in this order

1. [System design](SYSTEM_DESIGN.md): architecture, repository layout, agent semantics, simulator integration, UI, protocols, and configuration decisions.
2. [Research protocol](RESEARCH_PROTOCOL.md): questions, scenario suite, fair comparisons, metrics, analysis, validity, and publication requirements.
3. [Implementation plan](IMPLEMENTATION_PLAN.md): ordered engineering tasks with acceptance criteria.
4. [Configuration examples](examples/README.md): a hierarchy episode, a swarm episode, and an experiment sweep. They are design examples, not executable configurations for an existing runner.
5. [Contract definitions](CONTRACTS.md): implementation fields, invariants, and error categories for the process/API boundaries.
6. [Runtime audit](repo-audit.json) and [audit script](../../tools/audit_cyborg.py): evidence for the narrow multi-attacker compatibility fix and verified-address delivery bridge.
7. [Software validation plan](VALIDATION_PLAN.md): executable mission/organization acceptance fixtures, observed fixes, coverage and remaining limits.
8. [Phase 1–2 acceptance](PHASE_1_2_ACCEPTANCE.md): per-ticket closure, current test results, UI evidence and the Phase 3 boundary.

## Main decisions

- Build the research application in the parent AbstractCyberSim repository, with CybORG as a pinned dependency and a small documented compatibility patch.
- Use a segmented enterprise network, independent red workers, and a separate cognitive coordinator for hierarchy. Each worker owns its own simulator sessions and memory.
- Expose ordinary research settings in the UI; persist the same configuration for a headless runner. New algorithms, action semantics, metrics, and scenario generators remain code extensions.
- Separate the physical network, the communication topology, and each agent's knowledge. Display all three.
- Keep the legacy simulator in its existing Python 3.8 environment; use a modern Python service and browser UI through a process boundary.
- Run the same core research loop from both the UI and command line. The UI never determines experimental results.

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
