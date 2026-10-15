"""Apply the sole reviewed source patch, idempotently, at the pinned revision."""
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
COMMIT = "2742b5e0ce4330c9b14006b38acd3b5ebe00d6fd"


def main():
    vendor = ROOT / "CybORG"
    head = subprocess.check_output(["git", "-C", str(vendor), "rev-parse", "HEAD"], text=True).strip()
    if head != COMMIT:
        raise SystemExit("Refusing to patch a different engine revision")
    path = vendor / "CybORG/Simulator/Actions/ConcreteActions/Portscan.py"
    source = path.read_text(encoding="utf-8")
    old = "state.sessions['Red'][self.session]"
    if old not in source:
        if "from_host = state.hosts[state.sessions[self.agent][self.session].hostname]" not in source:
            raise SystemExit("Unexpected Portscan source; review manually")
        print("Engine patch already applied")
        return
    if source.count(old) != 2:
        raise SystemExit("Unexpected Portscan source; review manually")
    path.write_text(source.replace(old, "state.sessions[self.agent][self.session]"), encoding="utf-8")
    print("Applied multi-actor Portscan fix (two actor-ownership lookups)")


if __name__ == "__main__":
    main()
