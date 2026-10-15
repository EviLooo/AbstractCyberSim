"""Public mechanical eligibility for simulated actions; no world/engine imports.

Candidates deliberately include incompatible methods. Only the simulator can
decide compatibility. History and evidence guide policies, never this catalog.
"""
from packages.contracts.models import ActionProposal


def candidates(memory):
    view = memory.view
    if view.get("pending_action"):
        return []
    result = []
    own = [s for s in view.get("sessions", []) if s["active"]]
    controllers = [s for s in own if s["controller"]]
    own_names = {s["hostname"] for s in own}
    own_addresses = set()
    for hostid, host in memory.hosts.items():
        if host["fields"].get("System info", {}).get("Hostname") in own_names:
            if "." in hostid:
                own_addresses.add(hostid)
            own_addresses.update(str(i["IP Address"]) for i in host["fields"].get("Interface", []) if i.get("IP Address"))

    def add(action, target, source, **parameters):
        supporting = [r["evidence_id"] for r in memory.research_evidence
                      if r["host"] == target and (not r.get("source_host") or r["source_host"] == source["hostname"])]
        # A token's acquisition evidence lives on its storage host, not the
        # destination. Keep it last so the bounded citation list retains it.
        supporting.extend(r["evidence_id"] for r in memory.research_evidence
                          if parameters.get("token_ref") and r.get("token_ref") == parameters["token_ref"])
        result.append(ActionProposal(action=action, target=target, session=source["id"],
            source_host=source["hostname"], basis_evidence_ids=list(dict.fromkeys(supporting))[-16:], **parameters).model_dump())

    for session in own:
        add("InspectArtifacts", session["hostname"], session)
        if not session["controller"]:
            for source in controllers:
                if not session["privileged"]:
                    add("PrivilegeEscalate", session["hostname"], source)
                else:
                    add("EstablishPivot", session["hostname"], source)
    for source in controllers:
        cache = view["scan_cache"].get(str(source["id"]), {})
        for address in sorted(view["known"]["ip_address"]):
            if address in own_addresses or address == "127.0.0.1":
                continue
            add("DiscoverNetworkServices", address, source)
            for kind, port in (("connectivity", 80), ("connectivity", 22), ("service_behavior", 80), ("auth_policy", 22)):
                add("Probe", address, source, probe=kind, port=port)
            if address in cache:
                for method in ("web_rfi", "ssh_weak_auth"):
                    add("AttemptAccess", address, source, method=method)
                for ref in view.get("possessed_tokens", []):
                    add("AttemptAccess", address, source, method="credential_login", token_ref=ref)
        for subnet in sorted(view["known"]["subnet"]):
            add("DiscoverRemoteSystems", subnet, source)
    return result
