print(">>> RUNNING DOWNLOADER FROM:", __file__)
import os
import subprocess
from typing import Tuple, Optional, List

class DownloadError(Exception):
    pass

def download_audio(
    youtube_url: str,
    output_path: str = "output/audio.wav",
    sample_rate: int = 16000
) -> str:
    """
    Download best available audio or fallback to mp4 (format 18) if necessary, then convert to WAV with ffmpeg.
    Returns path to output WAV; raises DownloadError on failure.
    """
    import glob
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        audio_base = os.path.splitext(output_path)[0]
        # Try bestaudio as usual
        yt_cmd = [
            "yt-dlp",
            "-f", "bestaudio",
            "-o", audio_base + ".%(ext)s",
            youtube_url
        ]
        result = subprocess.run(yt_cmd)
        if result.returncode != 0:
            # Fallback to format 18 (mp4 with both audio and video)
            yt_cmd_fallback = [
                "yt-dlp",
                "-f", "18",
                "-o", audio_base + ".mp4",
                youtube_url
            ]
            result2 = subprocess.run(yt_cmd_fallback)
            if result2.returncode != 0:
                raise DownloadError(f"yt-dlp failed to download audio in both bestaudio and mp4 format.")
            input_audio = audio_base + ".mp4"
        else:
            # Find bestaudio file
            candidates = glob.glob(audio_base + ".*")
            candidates = [f for f in candidates if not f.endswith('.wav')]  # exclude old outputs
            if not candidates:
                raise DownloadError(f"No audio file found after yt-dlp for {youtube_url}")
            input_audio = candidates[0]  # pick 1st available
        # Convert to WAV
        ffmpeg_cmd = [
            "ffmpeg", "-y", "-i", input_audio, "-ar", str(sample_rate), output_path
        ]
        subprocess.run(ffmpeg_cmd, check=True)
        if not os.path.exists(output_path):
            raise DownloadError(f"FFmpeg did not produce output file {output_path}")
        return output_path
    except Exception as e:
        raise DownloadError(f"Audio download/convert failed: {e}")


def download_captions(youtube_url: str, output_path: str = "output/captions.vtt", sub_lang: str = "en") -> Optional[str]:
    """
    Download auto-generated or manual captions in the requested language (default 'en') to output_path using yt-dlp.
    Returns the path to the downloaded VTT file, or None if download fails or not found.
    """
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        # Download captions for the given language
        command = [
            "yt-dlp",
            "--skip-download",
            "--write-auto-sub",
            "--write-sub",
            "--sub-lang", sub_lang,
            "--sub-format", "vtt",
            "-o", output_path,
            youtube_url
        ]
        subprocess.run(command, check=True)

        # After download, glob output directory for *.vtt files
        import glob
        vtt_files = sorted(glob.glob(os.path.join(os.path.dirname(output_path), '*.vtt')))
        if vtt_files:
            print(f"[downloader.py] Found VTT files after download ({sub_lang}):", vtt_files)

    except Exception:
        return None
    # yt-dlp may append language code extensions
    import json
    alignment_log_path = '.cursor/debug.log'
    vtt_candidates = [output_path]
    suffixes = [f".{sub_lang}.vtt", f".{sub_lang}-US.vtt", ".vtt", f".vtt.{sub_lang}.vtt"]
    base, _ = os.path.splitext(output_path)
    for suf in suffixes:
        test_path = base + suf
        # Log each file candidate considered
        with open(alignment_log_path, 'a') as f:
            f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "FN1", "location": "downloader.py:93", "message": "Checking caption candidate file", "data": {"test_path": test_path, "exists": os.path.exists(test_path)}, "timestamp": __import__('time').time()}) + '\n')
        if os.path.exists(test_path):
            vtt_candidates.append(test_path)
    for candidate in vtt_candidates:
        with open(alignment_log_path, 'a') as f:
            f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "FN2", "location": "downloader.py:97", "message": "Returning caption file", "data": {"candidate": candidate, "exists": os.path.exists(candidate)}, "timestamp": __import__('time').time()}) + '\n')
        if os.path.exists(candidate):
            return candidate
    return None

def extract_captions_text(captions_file: str, text_output: str = "output/youtube_captions.txt") -> Optional[str]:
    """
    Extracts *all* captions from the input captions_file and writes as plain text to text_output, returns the full text.
    """
    import webvtt
    import re, os
    lines = []
    for caption in webvtt.read(captions_file):
        clean = re.sub(r'<.*?>', '', caption.text.replace('\n', ' ')).strip()
        if clean:
            lines.append(clean)
    full_text = " ".join(lines).strip()
    os.makedirs(os.path.dirname(text_output), exist_ok=True)
    with open(text_output, "w", encoding="utf-8") as f:
        f.write(full_text + "\n")
    return full_text



def extract_aligned_captions(
    captions_file: str,
    chunk_range: Tuple[float, float],
    text_output: str = "output/youtube_captions.txt"
) -> str:
    """
    Extracts and concatenates captions overlapping chunk_range (start,end seconds).
    Saves result to text_output. Returns captured string.
    Raises Exception if no captions overlap.
    """
    import webvtt
    start_sec, end_sec = chunk_range
    aligned_lines: List[str] = []
    import re
    #region agent log
    import json
    alignment_log_path = '.cursor/debug.log'
    with open(alignment_log_path, 'a') as f:
        f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "ALIGN1", "location": "downloader.py:118", "message": "Caption alignment window", "data": {"chunk_range": [start_sec, end_sec]}, "timestamp": __import__('time').time()}) + '\n')
    #endregion
    aligned_captions_debug = []
    saw_first_real = False
    for caption in webvtt.read(captions_file):
        cap_start, cap_end = caption.start_in_seconds, caption.end_in_seconds
        #region agent log
        with open(alignment_log_path, 'a') as f:
            f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "ALIGN1", "location": "downloader.py:121", "message": "Caption candidate", "data": {"cap_start": cap_start, "cap_end": cap_end, "text": caption.text[:100]}, "timestamp": __import__('time').time()}) + '\n')
        #endregion
        # Strictest include: caption must start AND end within chunk window, and end strictly before chunk_end
        if cap_start >= start_sec and cap_end < end_sec:
            clean = re.sub(r'<.*?>', '', caption.text.replace('\n', ' ')).strip()
            # Skip if generic (credit/short lines) at start of chunk or trailing label lines
            if (cap_start < start_sec + 10 and (not clean or len(clean) < 6 or any(x in clean.lower() for x in ["transcriber", "reviewer", "kind: captions", "webvtt", "language:", "www", ".com"]))) or clean == '' or re.search(r'\(.*\)', clean):
                continue
            if not saw_first_real:
                with open(alignment_log_path, 'a') as f:
                    f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "ALIGNSKIP", "location": "downloader.py:134", "message": "Using first real caption", "data": {"cap_start": cap_start, "clean_text": clean[:150]} , "timestamp": __import__('time').time()}) + '\n')
                saw_first_real = True
            aligned_lines.append(clean)
            aligned_captions_debug.append({"cap_start": cap_start, "cap_end": cap_end, "clean_text": clean[:150]})
        else:
            #region agent log
            with open(alignment_log_path, 'a') as f:
                f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "ALIGNSKIP", "location": "downloader.py:140", "message": "Caption skipped (out of window)", "data": {"cap_start": cap_start, "cap_end": cap_end, "start_sec": start_sec, "end_sec": end_sec, "text": caption.text[:100]}, "timestamp": __import__('time').time()}) + '\n')
            #endregion
    #region agent log
    with open(alignment_log_path, 'a') as f:
        f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "ALIGN1", "location": "downloader.py:126", "message": "Aligned captions result", "data": {"aligned_captions": aligned_captions_debug, "n_aligned": len(aligned_lines)}, "timestamp": __import__('time').time()}) + '\n')
    #endregion
    if not aligned_lines:
        raise Exception(f"No captions overlap chunk range {chunk_range}.")
    full_text = " ".join(aligned_lines).strip()
    os.makedirs(os.path.dirname(text_output), exist_ok=True)
    with open(text_output, "w", encoding='utf-8') as f:
        f.write(full_text + "\n")
    return full_text
