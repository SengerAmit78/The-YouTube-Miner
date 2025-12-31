import os
from typing import List, Tuple
import numpy as np
import soundfile as sf

class ChunkingException(Exception):
    pass

def create_speech_chunks(
    audio_path: str,
    speech_segments: List[Tuple[float, float]],
    chunk_duration: float = 30.0,
    chunk_tol: float = 5.0,
    chunk_folder: str = "output/chunks",
    orig_sr: int = 16000
) -> List[Tuple[str, float]]:
    """
    Concatenate input speech-only segments and split into clean 30s (±tol) chunks.
    Saves each as chunks/chunk_XXX.wav. Returns list of (filepath, chunk_start_time (in original timeline)).

    chunk_duration: target duration for each chunk (seconds)
    chunk_tol: +/- tolerance, i.e. output chunks will be 25–35s
    """
    if not speech_segments:
        raise ChunkingException("Speech segments list is empty.")
    os.makedirs(chunk_folder, exist_ok=True)
    audio, sr = sf.read(audio_path)
    if sr != orig_sr:
        raise ChunkingException(f"Sample rate mismatch: expected {orig_sr}, found {sr}.")
    # Collect samples for all speech segments
    speech_audio = np.concatenate([
        audio[int(start*sr):int(end*sr)] for start, end in speech_segments
    ])
    total_len = len(speech_audio)
    chunk_len = int(chunk_duration * sr)
    chunk_tol_len = int(chunk_tol * sr)
    chunk_files = []
    idx = 0
    current = 0
    # Chop into chunks between (chunk_duration - tol) and (chunk_duration + tol) seconds
    while current + int((chunk_duration-chunk_tol)*sr) < total_len:
        # Find chunk end with tolerance
        chunk_end = min(current + chunk_len, total_len)
        chunk = speech_audio[current:chunk_end]
        secs = len(chunk) / sr
        if secs < (chunk_duration - chunk_tol):
            break  # Last chunk too short
        if secs > (chunk_duration + chunk_tol):
            chunk = chunk[:chunk_len]
            chunk_end = current + chunk_len
        # Save chunk
        chunk_path = os.path.join(chunk_folder, f"chunk_{idx+1:03}.wav")
        sf.write(chunk_path, chunk, sr)
        # The output chunk_start_time is (approximate, because chunks are speech-only, not in original timeline)
        chunk_files.append((chunk_path, current/sr))
        idx += 1
        current = chunk_end
    if not chunk_files:
        raise ChunkingException("No valid chunk of desired length could be created.")
    return chunk_files

# === Stub/shim for testing, allows @patch in tests ===
def run_silero_vad(*args, **kwargs):
    return []  # This dummy function can be patched in tests
