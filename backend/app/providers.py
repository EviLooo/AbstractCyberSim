"""Local cognition providers. Scripted mode is explicitly not an LLM."""
import hashlib
import json
import os
import time
import httpx
from pydantic import ValidationError
from packages.contracts.models import ActionProposal
from backend.app.settings import ROOT


class BudgetExceeded(RuntimeError):
    pass


class Cognition:
    def __init__(self, config, transcript_path):
        self.config = config
        self.path = transcript_path
        self.used = 0
        self.calls = 0
        self.failures = 0
        self.unknown_usage = 0
        self.prompt_hashes = {}
        for role in ["worker", "coordinator"]:
            text = (ROOT / "prompts" / f"{role}.txt").read_text(encoding="utf-8")
            self.prompt_hashes[role] = hashlib.sha256(text.encode()).hexdigest()

    async def complete(self, role, actor, view, schema, fallback):
        if self.config.provider == "scripted":
            return fallback
        system = (ROOT / "prompts" / f"{role}.txt").read_text(encoding="utf-8")
        content = json.dumps(view, ensure_ascii=False, separators=(",", ":"))
        # Do not truncate into invalid JSON or silently erase observations.
        # Context overflow is explicit and the episode records the error.
        if len(content.encode()) > self.config.max_context_bytes:
            raise RuntimeError("Private context exceeds configured byte limit; increase the limit or implement an evidence-preserving summarizer")
        # One token per UTF-8 byte is a deliberately conservative reservation
        # for common byte/subword local models. Calls are serial so reservations
        # cannot race. Actual counts always settle the ledger.
        reserve = len((system + content).encode()) + len(json.dumps(schema).encode()) + self.config.max_output_tokens + 1024
        if self.used + reserve > self.config.max_team_tokens:
            raise BudgetExceeded("Insufficient remaining team budget to reserve this call")
        start = time.monotonic()
        record = {"role": role, "actor": actor, "model_requested": self.config.model, "prompt_hash": self.prompt_hashes[role], "input": view, "schema": schema, "reserved_tokens": reserve}
        self.calls += 1
        try:
            async with httpx.AsyncClient(timeout=self.config.timeout_seconds) as client:
                response = await client.post(os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/") + "/api/chat", json={"model": self.config.model, "messages": [{"role": "system", "content": system}, {"role": "user", "content": content}], "format": schema, "stream": False, "options": {"temperature": self.config.temperature, "num_predict": self.config.max_output_tokens}})
                response.raise_for_status()
                data = response.json()
            # Log actual response/usage before attempting to parse the decision.
            record["response"] = data
            if "prompt_eval_count" in data and "eval_count" in data:
                amount = int(data["prompt_eval_count"]) + int(data["eval_count"])
                self.used += amount
                record["charged_tokens"] = amount
            else:
                self.unknown_usage += 1
                self.used += reserve
                record.update(charged_tokens=reserve, usage_status="unknown_reserved")
            return json.loads(data["message"]["content"])
        except Exception as exc:
            self.failures += 1
            record["error"] = str(exc)
            if "charged_tokens" not in record:
                self.unknown_usage += 1
                self.used += reserve
                record.update(charged_tokens=reserve, usage_status="unknown_reserved")
            raise
        finally:
            record["latency_seconds"] = time.monotonic() - start
            with self.path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")

    async def worker(self, actor, view, preferred):
        supplied = dict(view, suggested_action=preferred)
        try:
            result = await self.complete("worker", actor, supplied, ActionProposal.model_json_schema(), preferred)
            return ActionProposal.model_validate(result).model_dump()
        except (ValidationError, json.JSONDecodeError) as exc:
            # One bounded format repair, charged and logged as a separate call.
            # Transport failures/timeouts are not silently retried to success.
            supplied["format_repair"] = {"error": str(exc), "instruction": "Return a valid action object matching the schema using only the original private context."}
            result = await self.complete("worker", actor, supplied, ActionProposal.model_json_schema(), preferred)
            return ActionProposal.model_validate(result).model_dump()

    async def coordinator(self, view, default):
        # The language model can choose task assignments; identity and sessions
        # remain bound by the runner and native gateway.
        schema = {"type": "object", "properties": {a: {"anyOf": [ActionProposal.model_json_schema(), {"type": "null"}]} for a in view["workers"]}, "additionalProperties": False}
        assignments = {a: v["proposal"] for a, v in default.items()}
        raw = await self.complete("coordinator", "Coordinator", view, schema, assignments)
        if not isinstance(raw, dict) or set(raw) - set(view["workers"]):
            raise ValueError("Invalid coordinator worker bindings")
        result = {}
        for actor, proposal in raw.items():
            if proposal is None:
                continue
            p = ActionProposal.model_validate(proposal).model_dump()
            # Forward only references actually delivered to the coordinator.
            reports = view["delivered_reports"]
            evidence = list(dict.fromkeys(e for r in reports for e in r["evidence_ids"]))
            result[actor] = {"proposal": p, "evidence_ids": evidence}
        return result

    def summary(self):
        return {"provider": self.config.provider, "calls": self.calls, "charged_tokens": self.used, "unknown_usage_calls": self.unknown_usage, "provider_failures": self.failures, "prompt_hashes": self.prompt_hashes, "is_llm": self.config.provider != "scripted"}
