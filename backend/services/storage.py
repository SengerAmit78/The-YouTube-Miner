import os
import json
from typing import Any, Dict

RUNS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "runs")
print(f"[DEBUG] RUNS_DIR resolved to: {RUNS_DIR}")

def ensure_runs_dir():
    if not os.path.exists(RUNS_DIR):
        os.makedirs(RUNS_DIR, exist_ok=True)

def run_state_path(run_id: str) -> str:
    return os.path.join(RUNS_DIR, f"{run_id}.json")

def save_run_state(run_id: str, state: Dict[str, Any]):
    ensure_runs_dir()
    path = run_state_path(run_id)
    print(f"[Save] Writing to {path}")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state, f)

def load_run_state(run_id: str) -> Dict[str, Any]:
    path = run_state_path(run_id)
    print(f"[Load] Reading from {path}")
    if not os.path.exists(path): return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
