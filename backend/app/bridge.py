"""Async child process; no CybORG import may cross into the service interpreter."""
import asyncio
import json
import os
from pathlib import Path
from packages.contracts.models import ENGINE_COMMIT
from backend.app.settings import ROOT, engine_python


class EngineBridge:
    def __init__(self, log_path: Path):
        self.log_path = log_path
        self.process = None
        self.counter = 0
        self.lock = asyncio.Lock()

    async def start(self):
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self.log = self.log_path.open("ab")
        try:
            self.process = await asyncio.create_subprocess_exec(engine_python(), "-u", str(ROOT / "packages/engine_worker/main.py"), cwd=str(ROOT), stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE, stderr=self.log, limit=8 * 1024 * 1024, env=dict(os.environ, PYTHONIOENCODING="utf-8"))
            hello = await self.call("hello")
            if hello["engine_commit"] != ENGINE_COMMIT or not hello["python"].startswith("3.8.") or hello["gym"] != "0.23.1" or hello["numpy"] != "1.21.6":
                raise RuntimeError("Engine versions differ from the reviewed lock")
            return hello
        except BaseException:
            await self.close()
            raise

    async def call(self, method, **params):
        async with self.lock:
            self.counter += 1
            request = {"version": "1.0", "id": self.counter, "method": method, "params": params}
            encoded = (json.dumps(request, ensure_ascii=False) + "\n").encode("utf-8")
            if len(encoded) > 8 * 1024 * 1024:
                raise ValueError("Engine request is too large")
            if not self.process or self.process.returncode is not None:
                raise RuntimeError("Engine is not running; see engine.stderr.log")
            try:
                self.process.stdin.write(encoded)
                await self.process.stdin.drain()
                line = await asyncio.wait_for(self.process.stdout.readline(), timeout=30)
                if not line:
                    raise RuntimeError("Engine exited; see engine.stderr.log")
                response = json.loads(line)
                if response.get("id") != self.counter or response.get("version") != "1.0":
                    raise RuntimeError("Engine protocol mismatch")
                if not response["ok"]:
                    raise RuntimeError(response["error"]["message"])
                return response["result"]
            except BaseException:
                # A timeout/cancelled read makes subsequent framing uncertain.
                # Kill the worker rather than advancing a misaligned protocol.
                if self.process.returncode is None:
                    self.process.kill()
                raise

    async def close(self):
        if self.process:
            if self.process.returncode is None:
                self.process.terminate()
            try:
                await asyncio.wait_for(self.process.wait(), 5)
            except TimeoutError:
                self.process.kill()
                await self.process.wait()
            self.process = None
        if hasattr(self, "log"):
            self.log.close()
