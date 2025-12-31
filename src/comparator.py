from typing import Optional
import difflib
import os

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import unicodedata
import re, json, time

def compare_transcripts(
    whisper_text: str,
    captions_text: str,
    output_path: str = "output/comparison.txt",
    chunk_start: float = 0.0,
    chunk_end: float = None,
    captions_file: str = None,
) -> None:
    """
    Compares Whisper transcript and YouTube captions text.
    - Uses semantic similarity over best matching caption segment
    - Outputs side-by-side diff, semantic, and surface similarity to file.
    - Highlights differences for transparency.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    def normalize_inner(txt):
        txt = unicodedata.normalize('NFKC', txt)
        txt = txt.lower()
        # Remove only standard ASCII punctuation, keep Unicode script (good for Hindi/Eng)
        txt = re.sub(r'[!-/:-@\[-`{-~]', '', txt)
        txt = re.sub(r'\s+', ' ', txt)
        return txt.strip()
    def deduplicate(lines, min_len=6):
        cleaned = []
        prev = None
        for line in lines:
            line = line.strip()
            if len(line) < min_len:
                continue
            if line != prev:
                cleaned.append(line)
                prev = line
        return cleaned
    def cosine(emb1, emb2):
        emb1, emb2 = np.array(emb1).reshape(1,-1), np.array(emb2).reshape(1,-1)
        return float(cosine_similarity(emb1, emb2)[0][0])
    model = SentenceTransformer('paraphrase-multilingual-mpnet-base-v2')
    norm_whisper = normalize_inner(whisper_text)
    norm_captions = normalize_inner(captions_text)
    #region agent log
    with open('.cursor/debug.log','a') as dbg:
        dbg.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "CMP1", "location": "comparator.py:16", "message": "Normalized comparison strings", "data": {"norm_whisper": norm_whisper[:200], "norm_captions": norm_captions[:200], "len_whisper": len(norm_whisper), "len_captions": len(norm_captions)}, "timestamp": time.time()}) + '\n')
    #endregion
    # ---- Main Comparison Output ----
    with open(output_path, "w", encoding='utf-8') as f:
        f.write("=== Whisper Transcript (normalized) ===\n")
        f.write(norm_whisper + "\n\n")
        # 1. SLIDING SEMANTIC WINDOW MATCH
        # Deduplicate captions lines first
        cap_lines = [normalize_inner(line) for line in captions_text.split('.') if line.strip()]
        cap_lines = deduplicate(cap_lines)
        cap_text = " ".join(cap_lines)
        captions_words = cap_text.split()
        whisper_emb = model.encode(norm_whisper, show_progress_bar=False)
        window_size = max(10, int(len(norm_whisper.split()) * 1.5))
        all_windows = []
        for start in range(0, len(captions_words)-window_size+1, 3):
            wnd = captions_words[start:start+window_size]
            wnd_text = " ".join(wnd)
            wnd_emb = model.encode(wnd_text, show_progress_bar=False)
            score = cosine(whisper_emb, wnd_emb)
            # Only keep windows of reasonable length
            length_ratio = len(wnd) / (len(norm_whisper.split()) + 1e-6)
            if 0.5 < length_ratio < 2.0:
                all_windows.append((score, wnd_text))
        if not all_windows:
            best_score = 0.0
            best_window_text = ""
        else:
            all_windows.sort(reverse=True, key=lambda x: x[0])
            # Take mean of top 3
            top_scores = [sim for sim, win in all_windows[:3]]
            top_windows = [win for sim, win in all_windows[:3]]
            best_score = np.mean(top_scores)
            best_window_text = "\n---\n".join(top_windows)
        # Normalize 0-1 to 0-100 percentage
        normalized_score = round(((best_score + 1) / 2) * 100, 2)
        f.write("=== Best-Matching Caption Window (semantic) ===\n")
        f.write(best_window_text + "\n\n")
        f.write(f"Mean Cosine Similarity (Semantic, top windows): {best_score:.4f}\n")
        f.write(f"Normalized Semantic Similarity Score: {normalized_score:.2f}%\n\n")
        # 2. Classic surface diff for diagnostics
        import difflib
        f.write("=== Surface Differences (word-level, best window) ===\n")
        diff = list(difflib.ndiff(norm_whisper.split(), best_window_text.split()))
        for token in diff:
            if token.startswith("- "):
                f.write(f"[-{token[2:]}-] ")
            elif token.startswith("+ "):
                f.write(f"{{+{token[2:]}+}} ")
            else:
                f.write(token[2:] + " ")
        f.write("\n\n")
        sm = difflib.SequenceMatcher(None, norm_whisper, best_window_text)
        similarity = sm.ratio() * 100
        f.write(f"SequenceMatcher Similarity (surface, best window): {similarity:.2f}%\n\n")
        # 3. Classic full-captions diagnostic
        f.write("=== YouTube Captions (full file, normalized) ===\n")
        f.write(norm_captions + "\n\n")
        sm_full = difflib.SequenceMatcher(None, norm_whisper, norm_captions)
        similarity_full = sm_full.ratio() * 100
        f.write(f"SequenceMatcher Similarity (surface, full file): {similarity_full:.2f}%\n")

# === Shim/Expose needed functions for testing ===
def normalize(text):
    import unicodedata, re
    text = unicodedata.normalize('NFKC', text)
    text = text.lower()
    text = re.sub(r'[!-/:-@\[-`{-~]', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def calculate_semantic_similarity(hyp_text, ref_text, model=None):
    model = model or SentenceTransformer('paraphrase-multilingual-mpnet-base-v2')
    hyp = normalize(hyp_text)
    ref = normalize(ref_text)
    hyp_emb = model.encode(hyp, show_progress_bar=False)
    ref_emb = model.encode(ref, show_progress_bar=False)
    cos = float(cosine_similarity(np.array(hyp_emb).reshape(1,-1), np.array(ref_emb).reshape(1,-1))[0][0])
    norm_score = round(((cos + 1) / 2) * 100, 2)
    return norm_score
