import torch
import numpy as np
import soundfile as sf
from typing import List, Tuple

class VADException(Exception):
    pass

def run_silero_vad(
    wav_path: str,
    sampling_rate: int = 16000,
    min_speech_sec: float = 0.4,
    min_silence_sec: float = 0.2,
    vad_window_sec: float = 0.05,
    device: str = "cpu"
) -> List[Tuple[float, float]]:
    """
    Apply Silero VAD to audio file to return speech segments (in seconds).
    Discards silence and music.
    Returns list of (start_time, end_time).
    Raises VADException if audio is missing or no speech detected.
    """
    # Read WAV
    try:
        wav, sr = sf.read(wav_path)
    except Exception as e:
        raise VADException(f"Failed to read WAV: {e}")
    if sr != sampling_rate:
        raise VADException(f"Expected sample rate {sampling_rate}, but got {sr}.")

    if len(wav.shape) > 1:  # stereo to mono
        wav = np.mean(wav, axis=1)
    if len(wav) < sampling_rate:  # less than 1 second
        raise VADException("Audio file too short for VAD.")

    print("[VAD-DEBUG] ENTRY", {"wav_path": wav_path})
    try:
        vad_model_tuple = torch.hub.load('snakers4/silero-vad', 'silero_vad', trust_repo=True)
        vad_model = vad_model_tuple[0]
        utils = vad_model_tuple[1]
        get_speech_timestamps = utils[0]
        import torchaudio
        if len(wav.shape) > 1:
            wav = np.mean(wav, axis=1)
        audio_mono = torch.tensor(wav, dtype=torch.float32)
        print("[VAD-DEBUG] PRE_CALL_GST", {"shape": str(audio_mono.shape)})
        try:
            speech_timestamps = get_speech_timestamps(audio_mono, vad_model, sampling_rate=sampling_rate)
            print("[VAD-DEBUG] POST_CALL_GST", {"result_type": str(type(speech_timestamps)), "len": len(speech_timestamps)})
        except Exception as call_exc:
            print("[VAD-DEBUG] GST_CALL_ERROR", {"type": str(type(call_exc)), "err": str(call_exc)})
            raise
        if not speech_timestamps:
            raise VADException("No speech detected in audio.")
        intervals = [
            (segment['start'] / sampling_rate, segment['end'] / sampling_rate)
            for segment in speech_timestamps
        ]
        print("[VAD-DEBUG] RETURNING_INTERVALS", {"intervals": intervals[:3]})
        return intervals
    except Exception as e:
        print("[VAD-DEBUG] EXCEPTION", {"type": str(type(e)), "err": str(e)})
        raise VADException(f"Silero VAD processing failed: {e}")

