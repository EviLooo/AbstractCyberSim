import solara
import networkx as nx
import plotly.graph_objects as go
from abms_cyber.visualization.portrayal import get_node_color, get_node_size, get_agent_color, get_agent_size, get_node_line_color, get_node_line_width

@solara.component
def NetworkView(model, current_step):
    G = model.network.graph
    
    # We need a stable layout. Spring layout with seed works, but better to cache it
    # For now, generate predictably
    pos = nx.spring_layout(G, seed=42)
    
    # 1. Prepare Edge Traces
    edge_x = []
    edge_y = []
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=1, color='#888'),
        hoverinfo='none',
        mode='lines')

    # 2. Prepare Node Traces
    node_x = []
    node_y = []
    node_text = []
    node_colors = []
    node_sizes = []
    node_line_widths = []
    node_line_colors = []
    
    for node_id in G.nodes():
        x, y = pos[node_id]
        node_x.append(x)
        node_y.append(y)
        
        cyber_node = model.network.get_node(str(node_id))
        node_text.append(str(node_id))
        
        # Override baseline sizes to make them readable in Plotly
        # Plotly marker sizes scale differently than matplotlib
        base_size = 35 if cyber_node.is_target else 25
        node_sizes.append(base_size)
        node_colors.append(get_node_color(cyber_node))
        node_line_widths.append(get_node_line_width(cyber_node))
        node_line_colors.append(get_node_line_color(cyber_node))

    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        text=node_text,
        textposition="middle center",
        textfont=dict(color='white', size=12),
        hoverinfo='text',
        marker=dict(
            showscale=False,
            color=node_colors,
            size=node_sizes,
            line=dict(width=node_line_widths, color=node_line_colors)
        ))

    # 3. Prepare Agent Traces
    agent_x = []
    agent_y = []
    agent_colors = []
    agent_hover = []
    
    for agent in model.agents:
        if agent.current_node:
            # Slightly offset the agent so it sits immediately next to the node label
            # rather than directly on top of it obscuring the number.
            ax, ay = pos[int(agent.current_node.id)]
            agent_x.append(ax + 0.05)
            agent_y.append(ay + 0.05)
            agent_colors.append(get_agent_color(agent))
            agent_hover.append(f"Agent {agent.unique_id}<br>Privilege: {agent.privilege_level}")

    agent_trace = go.Scatter(
        x=agent_x, y=agent_y,
        mode='markers',
        hovertext=agent_hover,
        hoverinfo='text',
        marker=dict(
            symbol="star",
            size=18,
            color=agent_colors,
            line=dict(width=1, color='black')
        ))

    # 4. Assemble Figure
    fig = go.Figure(data=[edge_trace, node_trace, agent_trace],
             layout=go.Layout(
                autosize=True,
                showlegend=False,
                hovermode='closest',
                margin=dict(b=10,l=10,r=10,t=10),
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
                )
    
    return solara.FigurePlotly(fig, dependencies=[current_step])
