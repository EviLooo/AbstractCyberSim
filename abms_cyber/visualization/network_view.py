import solara
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from abms_cyber.visualization.portrayal import get_node_color, get_node_size, get_agent_color, get_agent_size

@solara.component
def NetworkView(model):
    fig = Figure(figsize=(8, 6))
    ax = fig.subplots()
    
    # Get graph from environment
    G = model.network.graph
    
    # We need a stable layout. Spring layout with seed works, but better to cache it
    # For now, generate predictably
    pos = nx.spring_layout(G, seed=42)
    
    # Node colors and sizes based on state
    node_colors = []
    node_sizes = []
    for node_id in G.nodes:
        cyber_node = model.network.get_node(str(node_id))
        node_colors.append(get_node_color(cyber_node))
        node_sizes.append(get_node_size(cyber_node))
        
    # Draw base network
    nx.draw_networkx_edges(G, pos, ax=ax, alpha=0.5)
    nx.draw_networkx_nodes(G, pos, ax=ax, node_color=node_colors, node_size=node_sizes, edgecolors='black')
    nx.draw_networkx_labels(G, pos, ax=ax, font_size=8)
    
    # Overlay agents
    agent_x = []
    agent_y = []
    agent_colors = []
    agent_sizes = []
    
    for agent in model.agents:
        if agent.current_node:
            p = pos[int(agent.current_node.id)]
            agent_x.append(p[0])
            agent_y.append(p[1])
            agent_colors.append(get_agent_color(agent))
            agent_sizes.append(get_agent_size(agent))
            
    if agent_x:
        ax.scatter(agent_x, agent_y, s=agent_sizes, c=agent_colors, marker='^', zorder=10)
        
    ax.axis('off')
    
    return solara.FigureMatplotlib(fig)
