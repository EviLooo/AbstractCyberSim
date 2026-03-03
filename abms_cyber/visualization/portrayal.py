def get_node_color(node):
    if node.compromised:
        return "red"
    if node.scanned:
        return "yellow"
    return "green"

def get_node_size(node):
    return 300 if node.is_target else 150

def get_agent_color(agent):
    # In V0.1 we can distinguish by org type or privilege
    if agent.model.org_type == "swarm":
        return "blue"
    return "cyan" # Centralized worker

def get_agent_size(agent):
    return 100 + (agent.privilege_level * 50)
