
"""
Mesa Data Collector Configuration.
"""

from mesa.datacollection import DataCollector

def get_data_collector(model):
    return DataCollector(
        model_reporters={
            "Detection_Level": lambda m: m.detection_level,
            "Compromised_Nodes": lambda m: m.count_compromised(),
            "Steps": lambda m: m.steps
        },
        agent_reporters={
            "Action": lambda a: a.memory.action_history[-1] if a.memory.action_history else "None",
            "Privilege": "privilege_level"
        }
    )
