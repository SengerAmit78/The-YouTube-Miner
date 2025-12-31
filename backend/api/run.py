from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from backend.services.run_manager import start_pipeline_run

router = APIRouter(prefix="/run", tags=["run"])

class RunRequest(BaseModel):
    youtube_url: str
    language: str
    model_size: str
    chunk_index: Optional[int] = 0

class RunResponse(BaseModel):
    run_id: str
    message: str

@router.post("", response_model=RunResponse)
def start_run(request: RunRequest):
    run_args = request.dict()
    run_id = start_pipeline_run(run_args)
    return RunResponse(run_id=run_id, message="Run started.")
