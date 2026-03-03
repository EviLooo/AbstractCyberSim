
"""
CLI Entry Point for the package.
"""
import sys
import os

# Ensure the parent directory is in path so we can import abms_cyber
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if __name__ == "__main__":
    from abms_cyber.model.cyber_model import CyberModel
    # ... logic similar to main.py or just import main
    # For now, let's just point to main.py logic if needed, 
    # but the requirement asked for run.py here.
    pass
