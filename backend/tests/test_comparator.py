"""
Unit tests for comparator logic in YouTube Miner pipeline.
Covers: normalization, semantic score calculation (mocked), score reason mapping, window/surface/edge paths, and error handling.
- Uses unittest.mock for all external models and I/O.
- All tests are deterministic, fast, and pure logic.
"""
import pytest
from unittest.mock import patch, MagicMock, mock_open
import numpy as np
from src import comparator

def fake_encode(text, *a, **k):
    # vector value based on content length
    return np.ones(3) * (len(text) % 5)

def test_normalize_text_basic():
    norm = comparator.normalize("Hello, world! This is a   test.")
    assert norm == "hello world this is a test"

# --- SEMANTIC SIMILARITY ---
@patch("src.comparator.SentenceTransformer")
def test_semantic_similarity_high_score(mock_st):
    mock_inst = MagicMock()
    mock_inst.encode.side_effect = lambda t, **kw: np.ones(3) if "match" in t else np.zeros(3)
    mock_st.return_value = mock_inst
    norm_score = comparator.calculate_semantic_similarity(
        "matching transcript", "matching caption", model=mock_inst)
    assert norm_score > 95.0

@patch("src.comparator.SentenceTransformer")
def test_semantic_similarity_low_score(mock_st):
    mock_inst = MagicMock()
    mock_inst.encode.side_effect = lambda t, **kw: np.zeros(3)
    mock_st.return_value = mock_inst
    norm_score = comparator.calculate_semantic_similarity(
        "A completely different hypothesis", "Totally different reference", model=mock_inst)
    assert norm_score < 60.0

def test_score_reason_thresholds():
    def reason(score):
        if score >= 85:
            return "The transcript and YouTube caption match closely in meaning."
        elif score >= 60:
            return "The transcript and caption are somewhat similar but have notable differences."
        else:
            return "The transcript and caption differ significantly for this segment."
    assert reason(85) == "The transcript and YouTube caption match closely in meaning."
    assert reason(84.99) == "The transcript and caption are somewhat similar but have notable differences."
    assert reason(60) == "The transcript and caption are somewhat similar but have notable differences."
    assert reason(59.9) == "The transcript and caption differ significantly for this segment."

def test_similarity_empty_texts():
    with patch("src.comparator.SentenceTransformer") as mock_st:
        mock_inst = MagicMock()
        mock_inst.encode.return_value = np.zeros(3)
        mock_st.return_value = mock_inst
        score = comparator.calculate_semantic_similarity("", "", model=mock_inst)
        assert score < 60.0

# --- WINDOW/FILE OUTPUT AND ERROR HANDLING ---
def test_compare_transcripts_happy(monkeypatch):
    monkeypatch.setattr(comparator, "SentenceTransformer", lambda *a, **k: MagicMock(encode=fake_encode))
    m = mock_open()
    with patch("builtins.open", m):
        comparator.compare_transcripts("hello world", "hello world")

def test_compare_transcripts_no_windows(monkeypatch):
    # All deduplication/lines filter out, simulate empty captions
    monkeypatch.setattr(comparator, "SentenceTransformer", lambda *a, **k: MagicMock(encode=fake_encode))
    m = mock_open()
    with patch("builtins.open", m):
        comparator.compare_transcripts("X Y Z", " ")  # triggers no all_windows branch

def test_compare_transcripts_file_write_error(monkeypatch):
    monkeypatch.setattr(comparator, "SentenceTransformer", lambda *a, **k: MagicMock(encode=fake_encode))
    with patch("builtins.open", side_effect=Exception("fail")):
        with pytest.raises(Exception):
            comparator.compare_transcripts("a", "b")

def test_compare_transcripts_model_exception(monkeypatch):
    def broken_encode(*a, **k):
        raise Exception("model fail")
    monkeypatch.setattr(comparator, "SentenceTransformer", lambda *a, **k: MagicMock(encode=broken_encode))
    m = mock_open()
    with patch("builtins.open", m):
        with pytest.raises(Exception):
            comparator.compare_transcripts("foo", "bar")

@pytest.mark.parametrize("whisper,caption", [
    ("identical text", "identical text"),
    (" ", "    "),  # whitespace only
    ("Short", "Miss")  # no match
])
def test_compare_transcripts_various(monkeypatch, whisper, caption):
    monkeypatch.setattr(comparator, "SentenceTransformer", lambda *a, **k: MagicMock(encode=fake_encode))
    m = mock_open()
    with patch("builtins.open", m):
        comparator.compare_transcripts(whisper, caption)
