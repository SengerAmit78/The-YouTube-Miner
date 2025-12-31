from typing import Optional
import os

class TranscriptionError(Exception):
    pass

def transcribe_chunk(
    chunk_path: str,
    output_path: str = "output/whisper_transcript.txt",
    model_size: str = "tiny",
    compute_type: str = "cpu",
    language: str = "en"
) -> str:
    """
    Transcribe a chunk WAV file using faster-whisper (Whisper-Tiny model).
    Writes transcript to output_path.
    Returns transcript string.
    Raises TranscriptionError on failure or empty output.
    """
    #region agent log
    import json
    with open('.cursor/debug.log','a') as f:
        f.write(json.dumps({
            "sessionId": "debug-session",
            "runId": "run1",
            "hypothesisId": "A,B,D",
            "location": "transcriber.py:20",
            "message": "Function entry and input params",
            "data": {"chunk_path": chunk_path, "output_path": output_path, "model_size": model_size, "language": language, "compute_type": compute_type},
            "timestamp": __import__('time').time()
        }) + '\n')
    #endregion
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        raise TranscriptionError("faster-whisper is not installed.")
    if not os.path.exists(chunk_path):
        raise TranscriptionError(f"Chunk file {chunk_path} does not exist.")
    #region agent log
    with open('.cursor/debug.log','a') as f:
        f.write(json.dumps({
            "sessionId": "debug-session",
            "runId": "run1",
            "hypothesisId": "A,B",
            "location": "transcriber.py:26",
            "message": "Creating WhisperModel",
            "data": {"model_size": model_size, "device": compute_type},
            "timestamp": __import__('time').time()
        }) + '\n')
    #endregion
    model = WhisperModel(model_size, device=compute_type, compute_type="int8")
    #region agent log
    with open('.cursor/debug.log','a') as f:
        f.write(json.dumps({
            "sessionId": "debug-session",
            "runId": "run1",
            "hypothesisId": "B,E",
            "location": "transcriber.py:27",
            "message": "Calling transcribe",
            "data": {"chunk_path": chunk_path, "language": language},
            "timestamp": __import__('time').time()
        }) + '\n')
    #endregion
    transcript = ""
    asr_end_time = 0.0
    print(f"[DEBUG] Transcribing {chunk_path} with model_size={model_size}, device={compute_type}, language={language}")
    segments, _info = model.transcribe(chunk_path, beam_size=1, language=language)
    for segment in segments:
        transcript += segment.text.strip() + " "
        if hasattr(segment, 'end'):
            asr_end_time = max(asr_end_time, float(segment.end))
    transcript = transcript.strip()
    #region agent log
    with open('.cursor/debug.log','a') as f:
        f.write(json.dumps({
            "sessionId": "debug-session",
            "runId": "run1",
            "hypothesisId": "E",
            "location": "transcriber.py:31",
            "message": "Transcript result",
            "data": {"transcript_start": transcript[:200], "asr_end_time": asr_end_time},
            "timestamp": __import__('time').time()
        }) + '\n')
    #endregion
    if not transcript:
        raise TranscriptionError("Whisper ASR returned empty transcript.")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding='utf-8') as f:
        f.write(transcript + "\n")
    return transcript, asr_end_time

# ===== Exposure for patching in tests =====
try:
    from faster_whisper import WhisperModel
except ImportError:
    WhisperModel = None
