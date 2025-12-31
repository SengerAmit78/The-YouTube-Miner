import argparse
import sys
import os

from src.downloader import download_audio, download_captions, extract_aligned_captions
from src.vad import run_silero_vad, VADException
from src.chunker import create_speech_chunks, ChunkingException
from src.transcriber import transcribe_chunk, TranscriptionError
from src.comparator import compare_transcripts

def prepare_new_output_dir(base="output"):
    import shutil, time, os
    # Remove the existing output directory (if any)
    if os.path.exists(base):
        shutil.rmtree(base)
    # Create new unique run directory (with timestamp for clarity)
    run_id = time.strftime("run_%Y%m%d_%H%M%S")
    outdir = os.path.join(base, run_id)
    os.makedirs(outdir, exist_ok=True)
    return outdir

def main():
    parser = argparse.ArgumentParser(description="YouTube Miner: VAD & ASR Comparison Pipeline")
    parser.add_argument("url", type=str, help="YouTube video URL")
    parser.add_argument("--output-dir", type=str, default="output", help="Output directory")
    parser.add_argument("--sample-rate", type=int, default=16000, help="WAV sample rate (default: 16k)")
    parser.add_argument("--chunk-duration", type=float, default=30.0, help="Chunk duration in seconds (default: 30)")
    parser.add_argument("--select-chunk", type=int, default=0, help="Which chunk to select (default: 0)")
    parser.add_argument("--language", "-l", type=str, default="en", help="Target subtitles/audio language (e.g., en, hi, fr)")
    parser.add_argument("--model-size", type=str, default=None, help="Whisper model size: tiny, small, base, medium, large")
    parser.add_argument("--default-english-model", type=str, default="tiny", help="Default model size for English")
    parser.add_argument("--default-hindi-model", type=str, default="small", help="Default model size for Hindi")
    args = parser.parse_args()

    output_dir = prepare_new_output_dir()
    audio_path = os.path.join(output_dir, "audio.wav")
    captions_path = os.path.join(output_dir, "captions.vtt")

    print("[1] Downloading audio...")
    try:
        audio_file = download_audio(args.url, output_path=audio_path, sample_rate=args.sample_rate)
    except Exception as e:
        print(f"Audio download failed: {e}")
        sys.exit(1)
    print(f"  Audio saved to {audio_file}")

    print("[2] Downloading captions...")
    captions_file = download_captions(args.url, output_path=captions_path, sub_lang=args.language)
    #region agent log
    import json
    with open('.cursor/debug.log','a') as f:
        f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "FN3", "location": "main.py:36", "message": "Caption file after download_captions", "data": {"captions_file": captions_file, "exists": os.path.exists(captions_file) if captions_file else False}, "timestamp": __import__('time').time()}) + '\n')
    #endregion
    if not captions_file or not os.path.exists(captions_file):
        warning_msg = (
            f"No usable auto-generated captions found in this YouTube video for '{args.language}'.\n"
            f"- This video likely does not have {args.language} (auto) captions or subtitles enabled.\n"
            f"- No comparison between Whisper transcript and captions could be performed.\n"
            "- Try another video with CC/auto-captions for a full demo."
        )
        compare_path = os.path.join(output_dir, "comparison.txt")
        with open(compare_path, "w", encoding="utf-8") as f:
            f.write(warning_msg + "\n")
        print(warning_msg)
        print("No captions to compare; see comparison.txt for explanation.")

    print("[3] Running VAD...")
    try:
        speech_segments = run_silero_vad(audio_file, sampling_rate=args.sample_rate)
    except VADException as e:
        print(f"VAD failed: {e}")
        sys.exit(1)
    print(f"  Detected {len(speech_segments)} speech segment(s).")

    print("[4] Creating speech chunks...")
    chunk_dir = os.path.join(output_dir, "chunks")
    try:
        chunks = create_speech_chunks(
            audio_path=audio_file,
            speech_segments=speech_segments,
            chunk_duration=args.chunk_duration,
            chunk_tol=5.0,
            chunk_folder=chunk_dir,
            orig_sr=args.sample_rate
        )
    except ChunkingException as e:
        print(f"Chunking failed: {e}")
        sys.exit(1)
    print(f"  Created {len(chunks)} chunk(s).")

    chunk_idx = args.select_chunk
    if chunk_idx >= len(chunks):
        print(f"Requested chunk index {chunk_idx} out of range. Using first chunk.")
        chunk_idx = 0
    chunk_path, speech_offset = chunks[chunk_idx]
    chunk_duration = os.path.getsize(chunk_path) / (args.sample_rate * 2)  # WAV pcm16, mono
    print(f"  Using chunk #{chunk_idx}: {chunk_path}")

    print("[5] Transcribing selected chunk (Whisper-Tiny)...")
    transcript_path = os.path.join(output_dir, "whisper_transcript.txt")
    try:
        # Decide model size if not specified
        if args.model_size:
            model_size = args.model_size
        elif args.language == "hi":
            model_size = args.default_hindi_model
        else:
            model_size = args.default_english_model
        #region agent log
        import json
        with open('.cursor/debug.log','a') as f:
            f.write(json.dumps({
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "A,B,D",
                "location": "main.py:84",
                "message": "Calling transcribe_chunk",
                "data": {"chunk_path": chunk_path, "output_path": transcript_path, "language": args.language, "model_size": model_size},
                "timestamp": __import__('time').time()
            }) + '\n')
        #endregion
        
        whisper_text, asr_end_time = transcribe_chunk(chunk_path, output_path=transcript_path, language=args.language, model_size=model_size)
        #region agent log
        with open('.cursor/debug.log','a') as f:
            f.write(json.dumps({
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "C",
                "location": "main.py:86",
                "message": "Chunk info",
                "data": {"chunk_path": chunk_path, "chunk_size_bytes": __import__('os').path.getsize(chunk_path)},
                "timestamp": __import__('time').time()
            }) + '\n')
        #endregion
        # Ensure whisper_text is written in full
        with open(transcript_path, "w", encoding="utf-8") as x:
            x.write(whisper_text.strip() + "\n")
    except TranscriptionError as e:
        print(f"Transcription failed: {e}")
        sys.exit(1)
    print(f"  Transcript saved to {transcript_path}")

    # [6] Extracting full YouTube captions (no alignment)...
    caption_text_path = os.path.join(output_dir, "youtube_captions.txt")
    from src.downloader import extract_captions_text
    captions_text = extract_captions_text(captions_file, text_output=caption_text_path)
    print(f"  Captions (full file) saved to {caption_text_path}")

    # [7] Comparing ASR and captions...
    compare_path = os.path.join(output_dir, "comparison.txt")
    from src.comparator import compare_transcripts
    compare_transcripts(whisper_text, captions_text, output_path=compare_path)
    print(f"  Comparison saved to {compare_path}")

if __name__ == "__main__":
    main()

