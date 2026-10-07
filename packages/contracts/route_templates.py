"""Versioned synthetic template definitions shared without simulator dependencies."""
VERSION = "1.0"


def templates(options):
    return {
        "fast_ssh": {"service": "SSH", "port": 22, "privilege": "user",
                     "exploit_ticks": options["fast_exploit_ticks"],
                     "detection_probability": options["fast_detection_probability"]},
        "quiet_ftp": {"service": "FTP", "port": 21, "privilege": "user",
                      "exploit_ticks": options["quiet_exploit_ticks"],
                      "detection_probability": options["quiet_detection_probability"]},
        "privileged_ftp": {"service": "FTP", "port": 21, "privilege": "root",
                           "exploit_ticks": options["privileged_exploit_ticks"],
                           "detection_probability": options["privileged_detection_probability"]},
    }


def clue(template):
    """Limited service assessment: no ACLs, downstream inventory or success odds."""
    risk = template["detection_probability"]
    return {"version": VERSION, "source": "synthetic service assessment after own successful scan",
            "service": template["service"], "estimated_exploit_ticks": template["exploit_ticks"],
            "route_sensor_exposure": "high" if risk >= 0.7 else "low" if risk <= 0.2 else "medium",
            "service_account_hint": "privileged service" if template["privilege"] == "root" else "ordinary service",
            "limits": "No guarantee of exploit success, current access or whole-route cost"}
