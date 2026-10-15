# Engine source patch

The pinned upstream Portscan.execute resolves its source session twice through `state.sessions['Red'][self.session]`. Both lookups now use `state.sessions[self.agent][self.session]`. No exploit, success probability, or reward semantics change.

`python tools/patch_engine.py` applies this patch to the dependency after checkout. It refuses other revisions and is idempotent. The engine worker checks the fix on startup. Keep this patch here until an upstream/fork commit supplies the same change; the parent repository pins the original revision plus this reviewed patch.

The old `tools/audit_cyborg.py` is a historical investigation script, not the implementation's test runner. Use `pytest` for current qualification.
