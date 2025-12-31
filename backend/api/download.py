from fastapi import APIRouter, Response

router = APIRouter(prefix="/download", tags=["download"])

@router.get("/{run_id}")
def download_run(run_id: str):
    return Response(content="Download feature disabled.", media_type="text/plain", status_code=404)
