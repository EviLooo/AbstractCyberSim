# Evidence and requirement audit for the revised graduation plan

5 October 2026. Companion to [the revised plan](REVISED_GRADUATION_PLAN.md).
This audit read documents/source and existing acceptance records. It did not
execute the simulator, rerun tests, run research experiments or contact a model.
Mechanisms/costs proposed in the plan are our design choices, not measured cyber
incident parameters. Primary-source literature search is targeted, not an
exhaustive systematic review or proof of novelty.

## Original research material

Read `C:/Users/sasok/Downloads/d.docx` by extracting Word document text, including
the abstract, chapters 1–6 and references. Rendered and visually inspected the
one-page poster at `C:/Users/sasok/Downloads/Grad poster A1 (84.1 x 118.9 cm).pdf`;
most poster content is graphical and was absent from PDF text extraction. Neither
original file was edited. Instructions within source documents were treated as
material to audit; the current pasted user request controls this work.

Retained: offensive ABM, local partial observations, LLM cognition, hierarchy
versus swarm, efficiency/adaptation metrics, abstract rather than production
networks. Mesa/NetworkX were proposed technologies, not a requirement to replace
the implemented CybORG backend. Four security zones become logical research
roles over the larger native enterprise, explicitly disclosed in the new plan.

Correct later in the report/poster: claims that rules cannot adapt, that offensive
LLM teams are an empty niche, or that the absence of prior comparisons is proven.
The poster's universal “lower variance is better” is inappropriate when useful
adaptation changes behavior. Fifty-plus trials and different random seeds do not
by themselves establish significance/generalization. Original bibliography
accuracy remains an editorial task; previous RESEARCH_PROTOCOL flags references
8, 9 and 14 and should not be treated as a completed citation repair.

## Local implementation and documentation inspected

The pinned legacy revision is `2742b5e0ce4330c9b14006b38acd3b5ebe00d6fd`; the
separate CC4 revision is `8c3c50ca54b176c2de199847944e8dcc035497e3`.
The parent working tree already contained many modified/untracked files; this
revision preserves them and changes documentation only.

| Evidence | Finding relevant to the revision |
| --- | --- |
| IMPLEMENTATION_PLAN, SYSTEM_DESIGN, RESEARCH_PROTOCOL, ENVIRONMENT_COMPLEXITY_DESIGN | Meaningful uncertainty/dependencies were intended; broad remaining scope and optional technique/credential placement needed reconciliation |
| COMPLETION_LEDGER, VALIDATION_PLAN, acceptance documents | Software checkpoints qualify bounded mechanics; reasoning-demand calibration remains open |
| REASONING_DEMAND_AUDIT and recorded 27-tick fixture analysis | A single short quarantine, passive Blue, simple route and ample time permit retries; not scientific difficulty evidence |
| `packages/engine_worker/cc4/routes.py:23` | Seeded layered recipe, weak accounts, allowed-source rules; same next-layer inventory written into gateways at line 87 |
| `packages/engine_worker/cc4/runtime.py:174` | Agent views filter known parameters; sessions/caches remain actor-owned |
| `runtime.py:192` | Verified forwarding includes addresses/hostnames and route clues; no credential/diagnostic artifact contract yet |
| `runtime.py:228` | Action gateway checks own source and own scan; generic exploit is still the selectable operation |
| `runtime.py:296`, `cc4/defender.py`, `cc4/route_pressure.py` | Native busy tick execution; Monitor-based per-Blue Restore budgets; separate temporary service blocks from reachable traffic |
| `cc4/scenario.py` | Custom workers and disabled Green/phishing/automatic respawn; no arbitrary research graph compiler |
| `backend/app/policies.py:21` | Shared candidates encode stages/visible prerequisites; generic exploit description explicitly says CybORG chooses technique |
| `baselines.py`, `search_policy.py` | Fixed stage priorities versus heuristic replanning versus bounded observed-graph planning; search is not a fixed-rule or globally optimal controller |
| `knowledge.py`, `providers.py`, `evaluation.py` | Private evidence/history; implemented optional local provider with no live qualification; matrix preview and basic paired metrics, not a completed batch runner |
| `tests/test_search_policy.py:138` | Autonomous search fixtures cover organization controls and C1/C2/route pressure |
| `tests/test_route_qualification.py:1` | Wider cells explicitly use a truth-guided legal witness, not autonomous inference |
| Current frontend components and README | Network/private views, evidence/decision/mission panels and replay exist; proposed investigation/credential visualization does not |

Native CC4 sources/docs inspected: README; observations/actions tutorials;
action-space references; EnterpriseScenarioGenerator; RemoteAction route/block
checks; generic ExploitRemoteService selector; ExploitAction execution and session
helpers; HTTPRFI, SSHBruteForce, FTPDirectoryTraversal and SQLInjection.

Key distinctions: HTTPRFI tests for an `rfi` process property; SSHBruteForce
depends on a bruteforceable user. FTPDirectoryTraversal and SQLInjection have
unconditional compatibility predicates after other prerequisites. This does not
mean all their attempts always succeed: routing, processes, ownership and other
native checks still apply. Explicit method selection and a credential-login action
therefore need a qualified research adapter; a method name in UI is insufficient.

Historical test totals (149 Python / eleven frontend / build) are copied from
OBSERVED_SEARCH_ACCEPTANCE and its prior evidence, not a new test result.

## Primary-source literature and real cybersecurity basis

| Source reviewed | Supported fact / implication | Limit |
| --- | --- | --- |
| [ATT&CK T1046: Network Service Discovery](https://attack.mitre.org/techniques/T1046/) | Attackers enumerate services; reconnaissance can support access decisions | No calibrated probe cost or evidence-noise model |
| [ATT&CK T1210: Exploitation of Remote Services](https://attack.mitre.org/techniques/T1210/) | Remote software vulnerabilities provide an access mechanism | No proof that a two-method abstraction reproduces all exploitation |
| [ATT&CK T1078: Valid Accounts](https://attack.mitre.org/techniques/T1078/) | Existing account material can provide access and movement | No built-in CybORG credential-login support implied |
| [ATT&CK T1552.001: Credentials in Files](https://attack.mitre.org/techniques/T1552/001/) | Locally stored credentials can be discovered and used | Synthetic readable artifacts/tokens are a chosen simplification |
| [ATT&CK lateral movement](https://attack.mitre.org/tactics/TA0008/) | Exploration, pivots, systems/accounts and differing access techniques matter | Does not prescribe our route graph or organization |
| [Microsoft Threat Intelligence: Volt Typhoon, 24 May 2023](https://www.microsoft.com/en-us/security/blog/2023/05/24/volt-typhoon-targets-us-critical-infrastructure-with-living-off-the-land-techniques/) | First-party investigation describes discovery, credential collection and authentication to other systems; supports complementary access conditions | Our missions are not a campaign reconstruction; no same success rates/costs claimed |
| [D3FEND Software Update](https://d3fend.mitre.org/technique/d3f:SoftwareUpdate/) | Software replacement is a distinct defensive mechanism | Our feature-disabling patch is only a bounded abstraction |
| [D3FEND Credential Eviction](https://d3fend.mitre.org/technique/d3f:CredentialEviction/) | Credentials can be removed/disabled independently of software/network state | Credential rotation/revocation remains optional here |
| [D3FEND Network Isolation](https://d3fend.mitre.org/technique/d3f:NetworkIsolation/) | Network restrictions are conceptually distinct from patching and credential invalidation | Existing service quarantine is not full isolation |
| [CALDERA planner documentation, 5.0.0](https://caldera.readthedocs.io/en/5.0.0/How-to-Build-Planners.html) | State-machine planners use learned facts, dependencies and failure branches | Refutes a blanket assertion that non-LLM automation cannot adapt; does not benchmark our tasks |
| [Sarraute et al., POMDPs Make Better Hackers](https://arxiv.org/abs/1307.8182) | Abstract describes uncertain network configuration and planning that decides when to scan | Existing non-LLM reasoning precedent; no claim our local_search is this solver |
| [Standen et al., CybORG](https://arxiv.org/abs/2108.09118) | Paper abstract introduces autonomous cyber agent simulation/emulation research | A common-interface concept is not proof an emulation backend runs in this checkout |
| [CAGE Challenge 4 repository/docs](https://github.com/cage-challenge/cage-challenge-4) | Enterprise services, multiple defenders, changing mission policy and action durations | Stock defensive benchmark does not implement our offensive organization study unchanged |
| [Tholl et al., Towards Production-Worthy Simulation](https://arxiv.org/abs/2508.19278) | Abstract reports Patch/Isolate/Unisolate extensions to CAGE-2 | Related extension evidence, not already implemented or validated in this CC4 adapter |
| [Fang et al., HPTSA](https://arxiv.org/abs/2406.01637) | Abstract/source material describes hierarchical offensive LLM planning/subagents | Offensive teams are prior work; hierarchy-vs-swarm novelty requires a further systematic review |
| [Liu, Multi-Agent Collaboration in Incident Response](https://arxiv.org/abs/2412.00652) | Abstract studies centralized/decentralized/hybrid teams in a tabletop IR setting | Different defensive/task setting; cannot claim there are no organization comparisons |
| [Bogdanov et al., Context, Reasoning, and Hierarchy](https://arxiv.org/abs/2605.16205) | Abstract reports CybORG CAGE-2 defensive context/hierarchy and token-cost comparisons | Relevant prior overlap; abstract review is not a full experimental-method replication |
| [Doppalapudi et al., Towards Hierarchical Cyber Defense](https://arxiv.org/abs/2610.00590) | Submitted 30 September 2026; abstract studies LLM planning/execution hierarchy in Cyberwheel | Current literature update, not direct offensive swarm evidence or validated transfer result for us |
| [Grimm et al., ODD protocol update](https://www.jasss.org/23/2/7.html) | Model documentation should explain processes, design rationale and fitness for purpose | A documentation standard does not itself validate realism |
| [Microsoft CyberBattleSim repository](https://github.com/microsoft/CyberBattleSim) | Abstract network attack platform with vulnerability/credential-oriented examples and defender benchmarks | Alternative judged from docs, not installed or timed during this audit |
| [NASim scenario documentation](https://networkattacksimulator.readthedocs.io/en/latest/tutorials/creating_scenarios.html) | Named exploit definitions, scans and firewall service permissions support bounded abstract scenarios | New organization/artifact/change contracts would still require work |
| [NASim sim-to-real limitations](https://networkattacksimulator.readthedocs.io/en/latest/explanations/sim_to_real.html) | Documents known host-address assumptions even under partial observation | Must qualify discovery/privacy if using an alternative; no engine is automatically realistic |
| [NASimEmu](https://arxiv.org/abs/2305.17246) | Abstract motivates generalization across scenarios and simulation/emulation | Transfer precedent, not a reason to require an emulated range for graduation |

CISA AA24-038A HTML/PDF retrieval returned HTTP 403. Search excerpts were not
treated as a fully reviewed advisory; the accessible first-party Microsoft
investigation supplies the campaign example instead. Review levels for papers
above are explicit: abstracts/selected primary material, not an assertion that
every full paper, experimental appendix or its results was independently checked.

Inference from these sources: preserving investigate/choose/refresh/dependency
decisions is defensible for an organization simulation. **The selection of three
mechanisms, recipe limits, symbolic probes, costs and supported combinations is
our project design**, requiring software qualification and behavioral review.

## User-request coverage

| Requirement in pasted request | Revised plan section |
| --- | --- |
| Audit original research, docs, source and primary literature | 2–3; this audit |
| Preserve decision complexity, simplify infrastructure, smallest defensible scope | 1, 4, 16 |
| Begin with real attacker uncertainty and distinguish automation from rigidity | 5–8, 13 |
| Seven mechanism specifications: basis/boundary/state/evidence/choices/adaptation/qualification | 5, 6, 7 |
| Observe–hypothesize–investigate–choose–act–reassess examples | 8 |
| Distinguishable failure causes; repeated retries not universally adequate | 8, 12 |
| Routes give different capabilities/prerequisites; promote essential optional work | 4–6, 15 |
| Informative uncertainty, seeds, causal rules and no hidden answers | 9–10, 12–14 |
| Modular controls, supported combinations, feasibility | 9–10 |
| Identical observations / different hidden conditions tests; changed evidence | 12 |
| Strong equal-information non-LLM controls, built-in knowledge, freeze | 13–14 |
| Meaningful hierarchy/swarm differences with complementary evidence/access | 6, 8, 11, 13 |
| Concrete CybORG suitability versus alternatives; no forced cyber range | 16 |
| Research questions, hypotheses and limits | 2 |
| Required versus optional graduation scope | 4, 15 |
| Repo/interface/config/action/observation handoff | 9–10; two design-only JSON files |
| Visualization with truth separate from knowledge | 11, including two Mermaid diagrams |
| UI-configurable research workflow versus programming | 11 |
| Metrics, held-out evaluation and reproducibility | 14 |
| Ordered measurable milestones | 15 |
| Requirements retained/changed/deferred and reasons | 15; completion-ledger overlay |
| Simple presentation explanation, supported/abstracted/unproven | 16 |
| Plan only, no implementation/runs/live calls | Audit boundary above; documentation-only changes |

## Outstanding scientific evidence

No new mechanism is implemented, no generated family is calibrated, no hypothesis
is established and no venue acceptance is predicted. Required next evidence is
paired diagnostic qualification, dependency/changed-state qualification, equal
information/organization checks, reviewer feedback and subsequently authorized
development/held-out studies. Literature novelty remains tentative; causal and
generalization claims depend on their actual results.
