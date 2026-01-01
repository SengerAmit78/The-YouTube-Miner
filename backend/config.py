"""
Configuration file for YouTube Miner pipeline defaults.

This module centralizes all default configuration values used throughout
the pipeline, making it easy to modify settings without searching through
multiple files.
"""

# Audio Processing Configuration
DEFAULT_SAMPLE_RATE = 16000  # Hz - Standard for speech recognition
DEFAULT_CHUNK_DURATION = 30.0  # seconds - Target duration for audio chunks
DEFAULT_CHUNK_TOLERANCE = 5.0  # seconds - Tolerance for chunk duration (±5s)

# Output Configuration
DEFAULT_OUTPUT_DIR = "output"  # Base directory for all pipeline outputs
DEFAULT_RUNS_DIR = "runs"  # Directory for storing run state/metadata

# Language & Model Configuration
DEFAULT_LANGUAGE = "en"  # Default language code (ISO 639-1)
DEFAULT_MODEL_SIZE = "tiny"  # Default Whisper model size

# Language-specific model defaults
# Maps language codes to recommended Whisper model sizes
LANGUAGE_MODEL_MAP = {
    "en": "tiny",   # English - fast and accurate enough
    "hi": "small",  # Hindi - requires larger model for better accuracy
    # Add more language mappings as needed
    # "fr": "tiny",
    # "es": "tiny",
    # "de": "small",
}

def get_model_size_for_language(language: str) -> str:
    """
    Get the recommended Whisper model size for a given language.
    
    Args:
        language: ISO 639-1 language code (e.g., 'en', 'hi')
        
    Returns:
        Model size string ('tiny', 'small', 'base', 'medium', 'large')
    """
    return LANGUAGE_MODEL_MAP.get(language.lower(), DEFAULT_MODEL_SIZE)

# VAD (Voice Activity Detection) Configuration
VAD_SAMPLING_RATE = 16000  # Hz - Must match audio sample rate

# Transcription Configuration
DEFAULT_COMPUTE_TYPE = "int8"  # Whisper compute type (int8, float16, float32)
DEFAULT_BEAM_SIZE = 1  # Whisper beam search size (1 = greedy decoding, faster)

# File Naming Conventions
AUDIO_FILENAME = "audio.wav"
CAPTIONS_FILENAME = "captions.vtt"
TRANSCRIPT_FILENAME = "whisper_transcript.txt"
YOUTUBE_CAPTIONS_TEXT_FILENAME = "youtube_captions.txt"
COMPARISON_FILENAME = "comparison.txt"
CHUNKS_DIRNAME = "chunks"

# API Configuration (if needed)
# API_HOST = "0.0.0.0"
# API_PORT = 8000

# Pipeline Step Names (for status tracking)
PIPELINE_STEPS = [
    "downloading",
    "captioning", 
    "vad",
    "chunking",
    "done",
    "error"
]

