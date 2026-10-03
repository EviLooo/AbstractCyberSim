"""SQLite indexes immutable configuration + JSON run evidence on disk."""
import csv
import hashlib
import io
import json
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


class Store:
    def __init__(self, root: Path):
        self.root = root
        root.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.execute("CREATE TABLE IF NOT EXISTS runs (id TEXT PRIMARY KEY, metadata TEXT NOT NULL)")

    def connect(self):
        return sqlite3.connect(str(self.root / "index.sqlite"))

    def path(self, run_id):
        if not re.fullmatch(r"[a-f0-9]{32}", run_id):
            raise KeyError("Invalid run ID")
        return self.root / "runs" / run_id

    def write_json(self, path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False), encoding="utf-8")
        temporary.replace(path)

    def update(self, metadata):
        with self.connect() as db:
            db.execute("INSERT INTO runs VALUES (?, ?) ON CONFLICT(id) DO UPDATE SET metadata=excluded.metadata", (metadata["id"], json.dumps(metadata)))
        self.write_json(self.path(metadata["id"]) / "metadata.json", metadata)

    def get(self, run_id):
        self.path(run_id)
        with self.connect() as db:
            row = db.execute("SELECT metadata FROM runs WHERE id=?", (run_id,)).fetchone()
        if row is None:
            raise KeyError("Run not found")
        return json.loads(row[0])

    def list(self):
        with self.connect() as db:
            rows = db.execute("SELECT metadata FROM runs ORDER BY rowid DESC").fetchall()
        return [json.loads(r[0]) for r in rows]

    def recover(self):
        for m in self.list():
            if m["status"] not in ["completed", "stopped", "errored", "interrupted"]:
                m.update(status="interrupted", termination_reason="service_restart", updated_at=now())
                self.update(m)

    def save_frame(self, run_id, frame):
        self.write_json(self.path(run_id) / "frames" / f"{frame['tick']:06d}.json", frame)
        self.event(run_id, {"type": "frame", "tick": frame["tick"], "status": frame["status"]})

    def frame(self, run_id, tick=None):
        meta = self.get(run_id)
        if tick is None:
            tick = meta["tick"]
        if tick < 0 or tick > meta["tick"]:
            raise KeyError("Frame is not available")
        return json.loads((self.path(run_id) / "frames" / f"{tick:06d}.json").read_text(encoding="utf-8"))

    def event(self, run_id, event):
        event = dict(event, timestamp=now())
        with (self.path(run_id) / "events.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")

    def events(self, run_id, after=0):
        self.get(run_id)
        file = self.path(run_id) / "events.jsonl"
        if not file.exists():
            return {"cursor": 0, "items": []}
        rows = file.read_text(encoding="utf-8").splitlines()
        end = min(len(rows), after + 200)
        return {"cursor": end, "items": [dict(json.loads(rows[i]), sequence=i + 1) for i in range(after, end)]}

    def csv(self):
        output = io.StringIO()
        fields = ["id", "name", "status", "architecture", "workers", "world_id", "purpose", "manual_intervention", "tick", "termination_reason", "success", "charged_tokens", "invalid_actions", "duplicate_actions", "message_delivered", "message_dropped"]
        writer = csv.DictWriter(output, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for meta in self.list():
            writer.writerow(dict(meta, **meta.get("metrics", {})))
        return output.getvalue()
