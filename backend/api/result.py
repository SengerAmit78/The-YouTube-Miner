import os
from fastapi import APIRouter, Request
from backend.services.run_manager import get_run_result
from backend.services.pipeline_wrapper import process_chunk_for_comparison, PipelineRunError
from backend.config import DEFAULT_LANGUAGE, DEFAULT_MODEL_SIZE, CHUNKS_DIRNAME, TRANSCRIPT_FILENAME

router = APIRouter(prefix="/result", tags=["result"])

@router.get("/{run_id}")
def get_result(run_id: str):
    result = get_run_result(run_id)
    if not result:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Result unavailable or not finished.")
    output_dir = result.get("output_dir")
    base_name = os.path.basename(output_dir) if output_dir else run_id

    webm_url = wav_url = caption_url = None
    if output_dir and os.path.isdir(output_dir):
        files = os.listdir(output_dir)
        if "audio.webm" in files:
            webm_url = f"/output/{base_name}/audio.webm"
        if "audio.wav" in files:
            wav_url = f"/output/{base_name}/audio.wav"
        for file in files:
            if file.endswith(".vtt") or file.endswith(".srt"):
                caption_url = f"/output/{base_name}/{file}"

    chunkFiles = []
    chunk_dir = os.path.join(output_dir, CHUNKS_DIRNAME)
    if os.path.isdir(chunk_dir):
        for file in sorted(os.listdir(chunk_dir)):
            if file.endswith('.wav'):
                chunkFiles.append(f"/output/{base_name}/{CHUNKS_DIRNAME}/{file}")

    # Transcript download URL (shown only if file exists)
    transcript_path = os.path.join(output_dir, TRANSCRIPT_FILENAME)
    transcript_url = None
    if os.path.exists(transcript_path):
        transcript_url = f"/output/{base_name}/whisper_transcript.txt"

    return {
        "run_id": run_id,
        "webm_url": webm_url,
        "wav_url": wav_url,
        "caption_url": caption_url,
        "chunkFiles": chunkFiles,
        "transcript_url": transcript_url
    }

@router.post("/{run_id}/process_chunk")
async def process_chunk(run_id: str, request: Request):
    print(f"[DEBUG] process_chunk endpoint called for {run_id}")
    data = await request.json()
    chunk_path = data.get('chunk_path')
    print(f"[DEBUG] chunk_path: {chunk_path}")
    if not chunk_path:
        print("[ERROR] Missing chunk_path")
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Missing chunk_path")
    try:
        from backend.services.run_manager import get_run_result
        meta = get_run_result(run_id)
        chunk_filename = os.path.basename(chunk_path)
        output_dir = meta.get("output_dir")
        full_chunk_path = os.path.join(output_dir, CHUNKS_DIRNAME, chunk_filename)
        print(f"[DEBUG] Calling process_chunk_for_comparison with: chunk={full_chunk_path}, run_id={run_id}, youtube_url={meta['args'].get('youtube_url')}")
        cmp_result = process_chunk_for_comparison(
            run_id=run_id,
            chunk_path=full_chunk_path,
            youtube_url=meta['args'].get('youtube_url'),
            language=meta['args'].get('language', DEFAULT_LANGUAGE),
            model_size=meta['args'].get('model_size', DEFAULT_MODEL_SIZE),
        )
        print(f"[DEBUG] Chunk processing complete. Result: {cmp_result}")
        transcript_url = None
        transcript_path = cmp_result.get('transcript_file')
        if transcript_path and os.path.exists(transcript_path):
            base_name = os.path.basename(output_dir)
            transcript_url = f"/output/{base_name}/{TRANSCRIPT_FILENAME}"
        return {
            "compare_text": cmp_result.get("compare_text"),
            "similarity_percent": cmp_result.get("similarity_percent"),
            "transcript_url": transcript_url
        }
    except PipelineRunError as e:
        print(f"[ERROR] PipelineRunError: {str(e)}")
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        print(f"[ERROR] Failed to process chunk: {str(e)}")
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=f"Failed to process chunk: {str(e)}")
