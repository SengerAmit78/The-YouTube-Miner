from fastapi import APIRouter
from backend.services.run_manager import get_run_status

router = APIRouter(prefix="/status", tags=["status"])

@router.get("/{run_id}")
def get_status(run_id: str):
    return get_run_status(run_id)
