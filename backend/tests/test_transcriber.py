"""
Unit tests for transcriber logic in the YouTube Miner pipeline.
Covers ASR model selection, empty transcript handling, success/failure, and mocks all model/audio/file/ffmpeg IO.
Robustly patches all relevant paths: makedirs, model, audio, file.
"""
import pytest
from unittest.mock import patch, MagicMock

class DummyContext:
    def __enter__(self): return self
    def __exit__(self, *a): pass
    def decode(self, *a, **k): return []

class DummySegment:
    def __init__(self, text="foo bar", end=30.0):
        self.text = text
        self.end = end

def build_dummy_model(segments=None):
    class DummyModel:
        def transcribe(self, *a, **k):
            segs = segments if segments is not None else [DummySegment()]
            return (segs, {})
    return DummyModel()

@patch("src.transcriber.os.makedirs")
@patch("av.open", return_value=DummyContext())
@patch("src.transcriber.os.path.exists", return_value=True)
@patch("src.transcriber.WhisperModel", new_callable=lambda: lambda *a, **kw: build_dummy_model())
@patch("faster_whisper.WhisperModel", new_callable=lambda: lambda *a, **kw: build_dummy_model())
def test_transcriber_success_normal(mock_fw, mock_wm, mock_exists, mock_av_open, mock_makedirs, tmp_path):
    """Transcribe function returns expected text and end time (all imports/paths/mock)"""
    from src.transcriber import transcribe_chunk
    out_file = tmp_path / "fake_out.txt"
    transcript, asr_end_time = transcribe_chunk(
        chunk_path="fake_chunk.wav",
        output_path=str(out_file),
        model_size="tiny",
        compute_type="cpu",
        language="en"
    )
    assert "foo bar" in transcript
    assert asr_end_time == 30.0

@patch("src.transcriber.os.makedirs")
@patch("av.open", return_value=DummyContext())
@patch("src.transcriber.os.path.exists", return_value=True)
@patch("src.transcriber.WhisperModel", new_callable=lambda: lambda *a, **kw: build_dummy_model(segments=[]))
@patch("faster_whisper.WhisperModel", new_callable=lambda: lambda *a, **kw: build_dummy_model(segments=[]))
def test_transcriber_empty_transcript_error(mock_fw, mock_wm, mock_exists, mock_av_open, mock_makedirs, tmp_path):
    """Returns empty transcript: should raise error and not pass output"""
    from src.transcriber import transcribe_chunk, TranscriptionError
    out_file = tmp_path / "fake_out.txt"
    with pytest.raises(TranscriptionError):
        transcribe_chunk(
            chunk_path="fake_chunk.wav",
            output_path=str(out_file),
            model_size="tiny",
            compute_type="cpu",
            language="en"
        )

@patch("src.transcriber.os.makedirs")
@patch("av.open", return_value=DummyContext())
@patch("src.transcriber.os.path.exists", return_value=True)
@patch("faster_whisper.WhisperModel")
@patch("src.transcriber.WhisperModel")
def test_transcriber_model_selection(mock_wm, mock_fw, mock_exists, mock_av_open, mock_makedirs, tmp_path):
    """Checks correct model size is used (also robust to fast-exit errors)."""
    model_used = {}
    def fake_init(model_size, device, compute_type):
        model_used["size"] = model_size
        class DummyModel:
            def transcribe(self, *a, **k):
                return ([DummySegment()], {})
        return DummyModel()
    mock_wm.side_effect = fake_init
    mock_fw.side_effect = fake_init
    from src.transcriber import transcribe_chunk
    out_file = tmp_path / "out.txt"
    transcript, asr_end_time = transcribe_chunk(
        "chunk.wav", str(out_file), model_size="medium", compute_type="cpu", language="en")
    assert model_used["size"] == "medium"
    assert "foo bar" in transcript
"""
Notes:
- ALL WhisperModel / audio / ffmpeg / IO is fully mocked for CI-friendly test runs.
- You may extend for more edge paths if required by adding fixtures.
"""
