
import argparse
import traceback
import sys

try:
    from abms_cyber.model.cyber_model import CyberModel
    from abms_cyber.config.default_config import CyberConfig
except ImportError:
    traceback.print_exc()
    sys.exit(1)

def run_experiment(org_type, trials):
    print(f"Running Experiment: {org_type} for {trials} trials")
    for t in range(trials):
        model = CyberModel(org_type=org_type, config=CyberConfig())
        while model.running:
            model.step()
        print(f"Trial {t+1}: Steps={model.steps}, Detection={model.detection_level:.2f}, Compromised={model.count_compromised()}")

def main():
    parser = argparse.ArgumentParser(description="ABMS Cyber Simulation")
    parser.add_argument("--mode", type=str, default="experiment", choices=["experiment", "visualize"])
    parser.add_argument("--org", type=str, default="swarm", choices=["swarm", "centralized"])
    parser.add_argument("--trials", type=int, default=1)
    
    args = parser.parse_args()
    
    if args.mode == "experiment":
        run_experiment(args.org, args.trials)
    elif args.mode == "visualize":
        print("Launching Solara Visualization UI...")
        import subprocess
        import sys
        
        # Launch using subprocess to allow Solara to bind to the port cleanly
        try:
             subprocess.run([sys.executable, "-m", "solara", "run", "abms_cyber/visualization/app.py"], check=True)
        except KeyboardInterrupt:
             print("\nVisualization closed.")

if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
