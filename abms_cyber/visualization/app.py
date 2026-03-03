import solara
import pandas as pd
from abms_cyber.config.default_config import CyberConfig
from abms_cyber.model.cyber_model import CyberModel
from abms_cyber.visualization.network_view import NetworkView
from abms_cyber.visualization.charts import MetricsChart

# Global state for Solara Reactive UI
config = CyberConfig(num_agents=5)
# You can tweak config here if needed for visualization

class ModelWrapper:
    def __init__(self):
        self.model = CyberModel(config=config, org_type="swarm")
        self.running = False

# We use a singleton wrapper so Solara re-renders can access the same model instance
wrapper = ModelWrapper()
step_counter = solara.reactive(0)

@solara.component
def Page():
    # Dependency on step_counter makes this component re-render when it changes
    current_step = step_counter.value
    
    with solara.Column(style={"padding": "20px", "max-width": "1200px", "margin": "0 auto"}):
        solara.Markdown("# 🛡️ ABMS-LLM Cyber Simulation (V0.1)")
        solara.Markdown("Monitoring real-time Swarm organizational attacks on the network topology.")
        
        # --- Control Panel ---
        with solara.Row(justify="center"):
            solara.Button("Step", color="primary", on_click=step_model, disabled=not wrapper.model.running)
            solara.Button("Reset", color="error", on_click=reset_model)
            if not wrapper.model.running:
                 solara.Markdown(" **Simulation Ended** (Target Compromised or Detected)")
            
        with solara.Row():
             solara.Markdown(f"**Current Step:** {wrapper.model.steps}")
             solara.Markdown(f"**Detection Level:** {wrapper.model.detection_level:.2f} / {wrapper.model.config.max_detection_level}")
             solara.Markdown(f"**Compromised Nodes:** {wrapper.model.count_compromised()}")
             
        solara.HTML(tag="hr")
        
        # --- Visualization Views ---
        with solara.Row():
             with solara.Column(style={"flex": "1", "min-width": "600px"}):
                  solara.Markdown("### Network Topology")
                  NetworkView(wrapper.model)
                  
             with solara.Column(style={"flex": "1", "min-width": "400px"}):
                  solara.Markdown("### Live Metrics")
                  # We get the dataframe from Mesa's datacollector
                  if wrapper.model.steps > 0:
                      df = wrapper.model.datacollector.get_model_vars_dataframe()
                      # Need to manually inject steps if not the index, but datacollector usually sets index=step
                      df["Steps"] = df.index
                      MetricsChart(df)
                  else:
                      solara.Markdown("Awaiting first step data...")

def step_model():
    if wrapper.model.running:
        wrapper.model.step()
        step_counter.value += 1  # Trigger react re-render

def reset_model():
    # Re-instantiate the model completely
    wrapper.model = CyberModel(config=config, org_type="swarm")
    step_counter.value = 0 # Trigger re-render

# The entrypoint for `solara run`
@solara.component
def App():
     Page()
