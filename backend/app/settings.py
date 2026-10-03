import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = Path(os.environ.get("RESEARCH_DATA_DIR", str(ROOT / "artifacts"))).resolve()


def engine_python():
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
