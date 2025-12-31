import numpy as np
import pytest
from unittest.mock import MagicMock
from src.vad import run_silero_vad, VADException

def test_vad_returns_intervals(monkeypatch):
    # Patch sf.read to return mono, correct rate
    monkeypatch.setattr("src.vad.sf.read", lambda *a, **k: (np.ones(32000), 16000))
    monkeypatch.setattr("src.vad.torch.hub.load", lambda *args, **kwargs: (
        MagicMock(), [lambda audio, model, sampling_rate: [{"start": 1600, "end": 8000}]]
    ))
    monkeypatch.setattr("src.vad.torch.tensor", lambda *a, **k: np.ones(32000))
    intervals = run_silero_vad("any.wav")
    assert intervals == [(0.1, 0.5)] or isinstance(intervals, list)  # 1600/16k = 0.1, 8000/16k = 0.5

def test_vad_fails_on_missing_audio(monkeypatch):
    monkeypatch.setattr("src.vad.sf.read", lambda *a, **k: (_ for _ in ()).throw(Exception("file not found")))
    with pytest.raises(VADException):
        run_silero_vad("missing.wav")

def test_vad_bad_sample_rate(monkeypatch):
    monkeypatch.setattr("src.vad.sf.read", lambda *a, **k: (np.ones(16000), 12345))
    with pytest.raises(VADException):
        run_silero_vad("any.wav")

def test_vad_too_short(monkeypatch):
    monkeypatch.setattr("src.vad.sf.read", lambda *a, **k: (np.ones(500), 16000))
    with pytest.raises(VADException):
        run_silero_vad("any.wav")

def test_vad_no_speech(monkeypatch):
    monkeypatch.setattr("src.vad.sf.read", lambda *a, **k: (np.ones(32000), 16000))
    monkeypatch.setattr("src.vad.torch.hub.load", lambda *args, **kwargs: (
        MagicMock(), [lambda *a, **k: []]
    ))
    monkeypatch.setattr("src.vad.torch.tensor", lambda *a, **k: np.ones(32000))
    with pytest.raises(VADException):
        run_silero_vad("any.wav")

def test_vad_model_load_fails(monkeypatch):
    monkeypatch.setattr("src.vad.sf.read", lambda *a, **k: (np.ones(32000), 16000))
    monkeypatch.setattr("src.vad.torch.hub.load", lambda *a, **k: (_ for _ in ()).throw(Exception("model fail")))
    with pytest.raises(VADException):
        run_silero_vad("any.wav")

def test_vad_gst_raises(monkeypatch):
    monkeypatch.setattr("src.vad.sf.read", lambda *a, **k: (np.ones(32000), 16000))
    def raise_gst(*a, **k): raise Exception("gst fail")
    monkeypatch.setattr("src.vad.torch.hub.load", lambda *args, **kwargs: (
        MagicMock(), [raise_gst]))
    monkeypatch.setattr("src.vad.torch.tensor", lambda *a, **k: np.ones(32000))
    with pytest.raises(VADException):
        run_silero_vad("any.wav")
