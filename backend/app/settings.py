import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = Path(os.environ.get("RESEARCH_DATA_DIR", str(ROOT / "artifacts"))).resolve()


def engine_python(profile="enterprise_legacy"):
    if profile in ("enterprise_cc4", "enterprise_cc4_research"):
        explicit = os.environ.get("CYBORG_CC4_PYTHON")
        path = Path(explicit) if explicit else ROOT / ".engine/cc4/venv/Scripts/python.exe"
        if not path.is_file():
            raise RuntimeError("Run tools/setup_cc4.ps1 or set CYBORG_CC4_PYTHON to the isolated Python 3.12 environment")
        checkout = Path(os.environ.get("CYBORG_CC4_CHECKOUT", str(ROOT / ".engine/cc4/checkout")))
        if not (checkout / "CybORG/env.py").is_file():
            raise RuntimeError("CC4 checkout is missing; run tools/setup_cc4.ps1")
        return str(path)
    if profile != "enterprise_legacy":
        raise RuntimeError("Unknown engine profile")
    explicit = os.environ.get("CYBORG_PYTHON")
    if explicit:
        path = Path(explicit)
        if not path.is_file():
            raise RuntimeError("CYBORG_PYTHON does not point to an interpreter")
        return str(path)
    candidates = [ROOT / ".engine/Scripts/python.exe", Path.home() / "anaconda3/envs/cyborg38/python.exe"]
    for path in candidates:
        if path.is_file():
            return str(path)
    raise RuntimeError("Set CYBORG_PYTHON to the Python 3.8 engine environment; see README")
