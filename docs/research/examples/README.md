# Configuration examples

These files define the proposed configuration contract. The research runner, generators, policies, and UI described by them are not implemented yet. Do not invoke the current drone dashboard with these files.

- `hierarchy.episode.json`: four offensive workers plus a coordinator, mock cognition, four-zone branching world, bounded communication, and shared resource limits.
- `swarm.episode.json`: the same world/settings/workers with peer organization. The mode chooses the declared star/mesh communication graph, while transport capacity/delay/loss are held fixed.
- `comparison.experiment.json`: a proposed Cartesian experiment plan referencing the hierarchy profile, then overriding only named research factors. It contains 160 planned episodes.

In the implementation, both the UI and CLI load these contracts. A researcher adjusts a form or JSON file; a programmer implements new semantics in registered modules.

Planned commands, not currently available:

```text
research doctor
research validate configs/my_episode.json
research serve
research run configs/my_episode.json
research batch configs/my_experiment.json
research analyze artifacts/batches/<batch_id>
research export <run_or_batch_id>
```

Validation has two stages: structural schema validation, then semantic capability validation against installed policy/scenario/provider versions. A syntactically valid configuration is not executable unless its registry entries are implemented and qualified.

Environment and model secrets belong in local settings, outside these files. A real provider run selects an installed model preset with its actual identity and settings; `scripted_v1` is a mock provider ID, not a commercial model.

## Contract rules

- `schema_version` must be recognized; reject extra fields and unknown nested parameters.
- `team.workers` is a positive integer within the chosen profile's qualified limit.
- `organization=single` requires one worker; hierarchy/swarm must match supported policy IDs.
- `coordinator` is derived from organization, not independently enabled in swarm.
- Rates lie in [0,1]; limits and seeds have declared integer ranges.
- Native session ownership and scan caches are not editable by researcher messages.
- Manual intervention is permitted only in `mode=exploration`; batch evaluation profiles must have `allow_manual_intervention=false`.
- Objective ID/target roles must exist in the materialized world and be qualified for the action catalog.
- `routing=qualified_zone_policy_v1` is the proposed generic profile's tested access model; it is not a claim that this policy already exists.
- Provider request output reservations must fit per-call limits and the remaining team allowance; actual usage settles reservations.
- `topology=by_policy` resolves to a star for hierarchy and a mesh for swarm v1; the resolved graph is saved.
- Changing settings produces a new resolved-config hash/run; scientific runs are immutable.

The supplied examples use mock cognition so no API spending is implied. Their role is to communicate parameter names and expected behavior to the implementer.
