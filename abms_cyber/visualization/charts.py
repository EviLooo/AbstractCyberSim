import solara
import plotly.express as px
import pandas as pd

@solara.component
def MetricsChart(df: pd.DataFrame):
    if df.empty:
        return solara.Markdown("Waiting for data...")
        
    # We plot the detection level and compromised nodes vs Steps
    fig = px.line(
        df, 
        x="Steps", 
        y=["Detection_Level", "Compromised_Nodes"],
        title="Simulation Metrics Over Time"
    )
    
    fig.update_layout(
        autosize=True,
        margin=dict(l=20, r=20, t=40, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    return solara.FigurePlotly(fig, dependencies=[df])
