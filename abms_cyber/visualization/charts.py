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
    
    return solara.FigurePlotly(fig)
