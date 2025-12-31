import threading
import time
from typing import Dict, Any
from backend.services.pipeline_wrapper import run_initial_pipeline, PipelineRunError
from backend.services.storage import save_run_state, load_run_state

run_states: Dict[str, Dict[str, Any]] = {}
PIPELINE_STEPS = ["downloading", "captioning", "vad", "chunking", "done", "error"]

def update_pipeline_step(run_id: str, step: str):
    if run_id in run_states:
        run_states[run_id]["step"] = step
        save_run_state(run_id, run_states[run_id])

def background_run(run_args: dict, run_id: str):
    try:
        print(f"[Pipeline] Started for {run_id} with args: {run_args}")
        run_states[run_id]["step"] = "downloading"
        save_run_state(run_id, run_states[run_id])
        initial_args = run_args.copy()
        initial_args.pop("chunk_index", None)
        result = run_initial_pipeline(run_id=run_id, update_step_fn=lambda step: update_pipeline_step(run_id, step), **initial_args)
        run_states[run_id]["step"] = "done"
        run_states[run_id]["result"] = result
        run_states[run_id]["args"] = run_args  # Persist original args for chunk processing
        run_states[run_id]["error"] = None
        save_run_state(run_id, run_states[run_id])
        print(f"[Pipeline] Done for {run_id} -> {result}")
    except PipelineRunError as err:
        run_states[run_id]["step"] = "error"
        run_states[run_id]["error"] = str(err)
        save_run_state(run_id, run_states[run_id])
        print(f"[Pipeline ERROR] {run_id}: {err}")
    except Exception as e:
        run_states[run_id]["step"] = "error"
        run_states[run_id]["error"] = f"Unknown error: {e}"
        save_run_state(run_id, run_states[run_id])
        print(f"[Pipeline FATAL ERROR] {run_id}: {e}")

def start_pipeline_run(run_args: dict) -> str:
    run_id = f"run_{int(time.time())}"
    run_states[run_id] = {"step": "starting", "error": None, "result": None, "args": run_args}
    save_run_state(run_id, run_states[run_id])
    thread = threading.Thread(target=background_run, args=(run_args, run_id))
    thread.start()
    return run_id

def get_run_status(run_id: str):
    state = load_run_state(run_id)
    if not state:
        return {"run_id": run_id, "step": "not_found", "error_message": "No such run."}
    return {"run_id": run_id, "step": state["step"], "error_message": state["error"]}

def get_run_result(run_id: str):
    state = load_run_state(run_id)
    if not state or not state.get("result"):
        return None
    # Always attach args for downstream
    if "args" in state:
        state["result"]["args"] = state["args"]
    return state["result"]

def get_all_runs():
    return [
        {"run_id": rid, "step": st["step"], "args": st.get("args", {}), "result": st.get("result", None)}
        for rid, st in run_states.items()
    ]
