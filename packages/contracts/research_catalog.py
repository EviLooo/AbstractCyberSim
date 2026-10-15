"""Public mechanical rules shared by native worker and policies; no dependencies."""
PUBLIC_CATALOG = {
    "version": "minimal_access_v1",
    "methods": {
        "web_rfi": {"port": 80, "duration": 4, "rule": "Reachable HTTP service with external import enabled; grants its service account."},
        "ssh_weak_auth": {"port": 22, "duration": 4, "rule": "Reachable SSH service with a weak account; grants service account access."},
        "credential_login": {"port": 22, "duration": 2, "rule": "Reachable SSH service and a possessed, valid token for this host/account."},
    },
    "probes": {
        "connectivity": {"duration": 1, "rule": "Source-specific TCP handshake or timeout on a selected port."},
        "service_behavior": {"duration": 2, "rule": "HTTP external import response; requires reachable port 80."},
        "auth_policy": {"duration": 2, "rule": "SSH authentication methods; does not reveal password strength."},
    },
    "InspectArtifacts": {"duration": 2, "rule": "Read local notes using your own active session; root-only artifacts require privilege."},
    "artifacts": {"rule": "Notes provide local leads, account hints and claimed token scope. Claims may be outdated, invalid or wrong-scope; a successful action verifies current capability."},
    "local_actions": {"DiscoverNetworkServices": {"duration": 1, "rule": "Scan a known address from an owned controller; results stay in that controller's cache."},
                      "PrivilegeEscalate": {"duration": 2, "rule": "Native privilege action on an owned session."},
                      "EstablishPivot": {"duration": 2, "rule": "Create a controller from an owned privileged shell; cache starts empty."},
                      "DiscoverRemoteSystems": {"duration": 1, "rule": "Discover addresses in a known subnet from an owned controller."}},
    "uncertainty": "Compatibility and token scope remain unknown until legitimate evidence. Retry alone changes no condition.",
}
