"""Bounded privileged feasibility witness, NEVER an agent or comparator.

Runs an isolated native episode. It uses materialized truth to find a witness,
then performs every effect through legal actions. Failure means unverified,
not a proof of impossibility. No model calls or scientific estimates.
"""
import copy


def qualify(config):
    from packages.engine_worker.cc4.research.runtime import EngineRuntime
    runtime = EngineRuntime()
    frame = runtime.create(copy.deepcopy(config))
    world_id = frame["world"]["world_id"]
    roles = runtime.research.manifest["roles"]
    state = runtime.controller.state
    addresses = {role: str(next(ip for ip, host in state.ip_addresses.items() if host == hostname)) for role, hostname in roles.items()}
    transcript = []
    bound = min(config["schedule"]["max_ticks"], 256)

    def perform(label, target, session=0, **parameters):
        nonlocal frame
        if runtime.tick >= bound:
            raise ValueError("Witness reached bounded horizon")
        proposal = dict(action=label, target=target, session=session, **parameters)
        frame = runtime.step({"Red_0": proposal})
        while frame["views"]["Red_0"]["pending_action"]:
            if runtime.tick >= bound:
                raise ValueError("Witness interrupted at bounded horizon")
            frame = runtime.step({})
        record = next(r for r in frame["actions"] if r["actor"] == "Red_0")
        transcript.append(copy.deepcopy(record))
        if not record["valid"] or record["outcome"] != "TRUE":
            raise ValueError("Witness action failed: {} ({})".format(label, record.get("rejection") or record["outcome"]))
        return frame

    def owned(hostname, controller=False):
        return next(s["id"] for s in frame["views"]["Red_0"]["sessions"] if s["active"] and
                    s["hostname"] == hostname and (not controller or s["controller"]))

    def acquire(role, method, controller=False):
        perform("DiscoverNetworkServices", addresses[role])
        perform("AttemptAccess", addresses[role], method=method)
        if controller:
            perform("PrivilegeEscalate", roles[role])
            perform("EstablishPivot", roles[role])
        local = owned(roles[role], controller)
        perform("InspectArtifacts", roles[role], local)
        return local

    try:
        perform("InspectArtifacts", roles["entry"])
        # Privileged selection distinguishes genuine scope/validity only for
        # feasibility. Competing policies never receive this predicate.
        def token_for(host):
            return next((ref for ref in runtime.research.possession[runtime.bindings["Red_0"]]
                         if runtime.research.permits(runtime.bindings["Red_0"], ref, host)), None)
        token = token_for(roles["archive_target"])
        if not token:
            acquire("archive", "ssh_weak_auth")
            token = token_for(roles["archive_target"])
        source = 0
        if runtime.config["scenario"]["research"]["recipe"] == "combine" or runtime.research.manifest["variant"] == "source_denied":
            source = acquire("bridge", "web_rfi", True)
        perform("DiscoverNetworkServices", addresses["archive_target"], source)
        perform("AttemptAccess", addresses["archive_target"], source, method="credential_login", token_ref=token)
        perform("PrivilegeEscalate", roles["archive_target"], source)
        if config["scenario"]["research"]["recipe"] == "combine":
            app = acquire("app", "web_rfi", True)
            perform("DiscoverNetworkServices", addresses["parallel_target"], app)
            perform("AttemptAccess", addresses["parallel_target"], app, method="credential_login", token_ref=token_for(roles["parallel_target"]))
            perform("PrivilegeEscalate", roles["parallel_target"], app)
        # Include the complete declared defensive response in the witness. A
        # premature success before Restore is insufficient qualification.
        for _ in range(24):
            response = runtime.response
            if response.options["mode"] == "none" or response.used and response.inflight is None:
                break
            if runtime.tick >= bound:
                raise ValueError("Response cannot fit witness horizon")
            frame = runtime.step({})
        if roles["archive_target"] not in frame["score"]["privileged_hosts"]:
            perform("AttemptAccess", addresses["archive_target"], source, method="credential_login", token_ref=token)
            perform("PrivilegeEscalate", roles["archive_target"], source)
        hold = (config["scenario"].get("mission") or {}).get("hold_ticks", 1)
        for _ in range(hold):
            if frame["score"]["mission_success"]:
                break
            if runtime.tick >= bound:
                raise ValueError("Final hold exceeds horizon")
            frame = runtime.step({})
        if not frame["score"]["mission_success"]:
            raise ValueError("Witness did not satisfy native mission monitor")
        status, reason = "native_witness_validated", None
    except (ValueError, StopIteration) as error:
        status, reason = "unverified", str(error) or "Missing witness capability"
    return {"version": "1.0", "status": status, "reason": reason, "world_id": world_id,
            "ticks": runtime.tick, "native_step_count": runtime.controller.step_count,
            "access_resources": runtime.research.public_resources(), "witness": transcript,
            "final_score": copy.deepcopy(frame["score"]), "max_native_ticks": bound,
            "limitations": "One privileged bounded witness; not exhaustive planning, realistic difficulty, or scientific performance."}
