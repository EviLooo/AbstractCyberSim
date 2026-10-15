"""Bounded JSONL protocol; all native/library output is routed to stderr."""
import contextlib
import argparse
import os
import json
import platform
import subprocess
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
MAX_FRAME = 8 * 1024 * 1024


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", choices=["enterprise_legacy", "enterprise_cc4", "enterprise_cc4_research"], default="enterprise_legacy")
    profile = parser.parse_args().profile
    checkout = Path(os.environ.get("CYBORG_CC4_CHECKOUT", str(ROOT / ".engine/cc4/checkout"))) if profile in ("enterprise_cc4", "enterprise_cc4_research") else ROOT / "CybORG"
    sys.path.insert(0, str(checkout.resolve()))
    wire = sys.stdout
    with contextlib.redirect_stdout(sys.stderr):
        import gym
        import numpy
        if profile == "enterprise_cc4_research":
            from packages.engine_worker.cc4.research.runtime import EngineRuntime
        elif profile == "enterprise_cc4":
            from packages.engine_worker.cc4.runtime import EngineRuntime
        else:
            from packages.engine_worker.runtime import EngineRuntime
        runtime = EngineRuntime()
    while True:
        line = sys.stdin.buffer.readline(MAX_FRAME + 1)
        if not line:
            break
        request = {}
        try:
            if len(line) > MAX_FRAME or not line.endswith(b"\n"):
                raise ValueError("Protocol frame exceeds limit")
            request = json.loads(line)
            if set(request) != {"version", "id", "method", "params"} or request["version"] != "1.0":
                raise ValueError("Unknown protocol fields or version")
            method, params = request["method"], request["params"]
            with contextlib.redirect_stdout(sys.stderr):
                if method == "hello":
                    import CybORG
                    if profile in ("enterprise_cc4", "enterprise_cc4_research") and not Path(CybORG.__file__).resolve().is_relative_to(checkout.resolve()):
                        raise ValueError("Simulator import did not come from the configured checkout")
                    result = {"version": "1.0", "python": platform.python_version(), "gym": gym.__version__, "numpy": numpy.__version__, "engine_commit": subprocess.check_output(["git", "-C", str(checkout), "rev-parse", "HEAD"], universal_newlines=True).strip(), "capabilities": [profile, "joint_step", "verified_intel", "snapshot"], "upstream_dirty": bool(subprocess.check_output(["git", "-C", str(checkout), "status", "--porcelain"], universal_newlines=True).strip())}
                elif method == "create":
                    result = runtime.create(params["config"])
                elif method == "qualify" and profile == "enterprise_cc4_research":
                    from packages.engine_worker.cc4.research.qualification import qualify
                    result = qualify(params["config"])
                elif method == "step":
                    result = runtime.step(params["proposals"])
                elif method == "ingest_intel":
                    result = runtime.ingest_intel(**params)
                elif method == "close":
                    result = {"closed": True}
                else:
                    raise ValueError("Unknown engine method")
            response = {"version": "1.0", "id": request["id"], "ok": True, "result": result}
        except Exception as exc:
            traceback.print_exc(file=sys.stderr)
            response = {"version": "1.0", "id": request.get("id"), "ok": False, "error": {"type": type(exc).__name__, "message": str(exc)}}
        wire.write(json.dumps(response, ensure_ascii=False, allow_nan=False) + "\n")
        wire.flush()
        if request.get("method") == "close":
            break


if __name__ == "__main__":
    main()
