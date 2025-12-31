import os
import shutil
import time
from src.downloader import download_audio, download_captions, extract_aligned_captions, extract_captions_text
from src.vad import run_silero_vad, VADException
from src.chunker import create_speech_chunks, ChunkingException
from src.transcriber import transcribe_chunk, TranscriptionError
from src.comparator import compare_transcripts

class PipelineRunError(Exception):
    pass

def prepare_new_output_dir(run_id: str, base="output"):
    outdir = os.path.join(base, run_id)
    os.makedirs(outdir, exist_ok=True)
    return outdir

# Initial run: only preprocessing, chunking, no transcription/comparison
def run_initial_pipeline(run_id: str, youtube_url, language, model_size, sample_rate=16000, chunk_duration=30.0, base_output_dir="output", update_step_fn=None):
    output_dir = prepare_new_output_dir(run_id, base_output_dir)
    if update_step_fn: update_step_fn("downloading")
    audio_path = os.path.join(output_dir, "audio.wav")
    # Find the caption file in output directory after download
    captions_path = None
    try:
        print(f"[DEBUG] Initial download_audio: {youtube_url} -> {audio_path}")
        audio_file = download_audio(youtube_url, output_path=audio_path, sample_rate=sample_rate)
        if update_step_fn: update_step_fn("vad")
    except Exception as e:
        print(f"[ERROR] Audio download failed: {e}")
        raise PipelineRunError(f"Audio download failed: {e}")
    # Download captions, but don't assume file name
    download_captions(youtube_url, output_path=os.path.join(output_dir, "captions.vtt"), sub_lang=language)
    # Find any .vtt or .srt file
    for file in os.listdir(output_dir):
        if file.endswith(".vtt") or file.endswith(".srt"):
            captions_path = os.path.join(output_dir, file)
            break
    if not captions_path:
        print("[ERROR] No captions to compare; processing stops.")
        return {
            "run_id": run_id,
            "output_dir": output_dir,
            "error": "No captions to compare; see output directory for details."
        }
    try:
        print(f"[DEBUG] Running VAD on {audio_file}")
        speech_segments = run_silero_vad(audio_file, sampling_rate=sample_rate)
        if update_step_fn: update_step_fn("chunking")
    except VADException as e:
        print(f"[ERROR] VAD failed: {e}")
        raise PipelineRunError(f"VAD failed: {e}")
    chunk_dir = os.path.join(output_dir, "chunks")
    try:
        print(f"[DEBUG] Creating speech chunks in {chunk_dir}")
        chunks = create_speech_chunks(
            audio_path=audio_file,
            speech_segments=speech_segments,
            chunk_duration=chunk_duration,
            chunk_tol=5.0,
            chunk_folder=chunk_dir,
            orig_sr=sample_rate
        )
        print(f"[DEBUG] Created {len(chunks)} chunks.")
    except ChunkingException as e:
        print(f"[ERROR] Chunking failed: {e}")
        raise PipelineRunError(f"Chunking failed: {e}")
    return {
        "run_id": run_id,
        "output_dir": output_dir
    }

# --- Helper: Parse compare_result for reasons ---
def parse_compare_result(compare_result: str):
    lines = compare_result.splitlines()
    asr = []
    caption = []
    in_asr = False
    in_caption = False
    for line in lines:
        if "Whisper Transcript" in line:
            in_asr = True
            in_caption = False
            continue
        if "Best-Matching Caption Window" in line:
            in_caption = True
            in_asr = False
            continue
        if "===" in line:
            in_asr = False
            in_caption = False
            continue
        if in_asr:
            asr.append(line)
        if in_caption:
            caption.append(line)
    return " ".join(asr).strip(), " ".join(caption).strip()

# On-demand chunk process for transcript+compare
def process_chunk_for_comparison(run_id: str, chunk_path: str, youtube_url: str, language: str, model_size: str, base_output_dir="output"):
    output_dir = prepare_new_output_dir(run_id, base_output_dir)
    transcript_path = os.path.join(output_dir, "whisper_transcript.txt")
    chunk_file = os.path.normpath(chunk_path)
    print(f"[DEBUG] [PROCESS] Starting transcript & compare for CHUNK: {chunk_file}")
    # Transcribe
    try:
        whisper_text, asr_end_time = transcribe_chunk(
            chunk_file,
            output_path=transcript_path,
            language=language,
            model_size=model_size or "tiny"
        )
        with open(transcript_path, "w", encoding="utf-8") as x:
            x.write(whisper_text.strip() + "\n")
        print(f"[DEBUG] Wrote transcript to: {transcript_path}")
    except TranscriptionError as e:
        print(f"[ERROR] Transcription failed for {chunk_file}: {e}")
        raise PipelineRunError(f"Transcription failed: {e}")
    # Find the captions file for comparison (.vtt or .srt)
    captions_file = None
    for file in os.listdir(output_dir):
        if file.endswith(".vtt") or file.endswith(".srt"):
            captions_file = os.path.join(output_dir, file)
            break
    if not captions_file or not os.path.exists(captions_file):
        raise PipelineRunError("No caption file (.vtt or .srt) found for comparison.")
    caption_text_path = os.path.join(output_dir, "youtube_captions.txt")
    if not os.path.exists(caption_text_path):
        extract_captions_text(captions_file, text_output=caption_text_path)
    with open(caption_text_path, "r", encoding="utf-8") as f:
        captions_text = f.read()
    compare_path = os.path.join(output_dir, "comparison.txt")
    compare_transcripts(whisper_text, captions_text, output_path=compare_path)
    compare_result = None
    similarity_percent = None
    with open(compare_path, "r", encoding="utf-8") as f:
        compare_result = f.read()
        for line in compare_result.splitlines():
            if "Normalized Semantic Similarity Score" in line:
                parts = line.split(":")
                if len(parts) > 1:
                    sim_value = parts[1].replace('%', '').strip()
                    try:
                        similarity_percent = float(sim_value)
                    except Exception:
                        similarity_percent = None
    asr_text, caption_text = parse_compare_result(compare_result)
    print(f"[DEBUG] Wrote comparison file: {compare_path}\n[DEBUG] Compare result preview: {compare_result[:100]}\n[DEBUG] Similarity: {similarity_percent}")
    return {
        "run_id": run_id,
        "output_dir": output_dir,
        "transcript_file": transcript_path,
        "compare_file": compare_path,
        "similarity_percent": similarity_percent,
        "compare_text": compare_result,
        "asr_text": asr_text,
        "caption_text": caption_text
    }
