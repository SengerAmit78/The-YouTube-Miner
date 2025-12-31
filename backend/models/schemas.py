from pydantic import BaseModel
from typing import Optional, Any, Dict, List

class RunRequest(BaseModel):
    youtube_url: str
    language: str
    model_size: str
    chunk_index: Optional[int] = None

class RunResponse(BaseModel):
    run_id: str
    message: str

class StatusResponse(BaseModel):
    run_id: str
    step: str
    error_message: Optional[str] = None
    logs: Optional[str] = None

class ResultResponse(BaseModel):
    run_id: str
    transcript: str
    best_caption_window: Optional[str] = None
    similarity_percent: Optional[float] = None
    metrics: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None

class RunItem(BaseModel):
    run_id: str
    youtube_url: str
    started_at: str
    status: str

class HistoryResponse(BaseModel):
    runs: List[RunItem]
