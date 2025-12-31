import pytest
from unittest.mock import patch, mock_open, MagicMock
import src.downloader as downloader

# --- download_audio ---
def test_download_audio_success_bestaudio():
    with patch('src.downloader.os.makedirs'), \
         patch('src.downloader.os.path.exists', return_value=True), \
         patch('src.downloader.subprocess.run') as mock_run, \
         patch('glob.glob', return_value=['output/audio.mp3']):
        mock_run.return_value.returncode = 0
        out = downloader.download_audio('http://fake.url/vid', 'output/audio.wav')
        assert out == 'output/audio.wav'
        assert mock_run.call_count == 2  # yt-dlp and ffmpeg

def test_download_audio_fallback_mp4():
    with patch('src.downloader.os.makedirs'), \
         patch('src.downloader.os.path.exists', return_value=True), \
         patch('src.downloader.subprocess.run') as mock_run, \
         patch('glob.glob', return_value=['output/audio.mp3']):
        mock_run.side_effect = [MagicMock(returncode=1), MagicMock(returncode=0), MagicMock(returncode=0)]
        out = downloader.download_audio('http://fake.url/vid', 'output/audio.wav')
        assert out == 'output/audio.wav'

def test_download_audio_all_fail():
    with patch('src.downloader.os.makedirs'), \
         patch('src.downloader.os.path.exists', return_value=True), \
         patch('src.downloader.subprocess.run') as mock_run, \
         patch('glob.glob', return_value=['output/audio.mp3']):
        mock_run.side_effect = [MagicMock(returncode=1), MagicMock(returncode=1)]
        with pytest.raises(downloader.DownloadError):
            downloader.download_audio('http://fake.url/vid', 'output/audio.wav')

def test_download_audio_ffmpeg_missing_output():
    with patch('src.downloader.os.makedirs'), \
         patch('src.downloader.os.path.exists', side_effect=lambda p: False), \
         patch('src.downloader.subprocess.run') as mock_run, \
         patch('glob.glob', return_value=['output/audio.mp3']):
        mock_run.return_value.returncode = 0
        with pytest.raises(downloader.DownloadError):
            downloader.download_audio('http://fake.url/vid', 'output/audio.wav')

# --- download_captions ---
def test_download_captions_file_found():
    with patch('src.downloader.os.makedirs'), \
         patch('src.downloader.subprocess.run'), \
         patch('glob.glob', return_value=['output/fake.en.vtt']), \
         patch('src.downloader.os.path.exists', return_value=True), \
         patch('src.downloader.open', mock_open()):
        out = downloader.download_captions('http://fake.url/vid', 'output/fake.vtt', 'en')
        assert out is not None

def test_download_captions_command_fail():
    with patch('src.downloader.os.makedirs'), \
         patch('src.downloader.subprocess.run', side_effect=Exception()), \
         patch('glob.glob', return_value=[]):
        out = downloader.download_captions('http://fake.url/vid', 'output/fake.vtt', 'en')
        assert out is None

def test_download_captions_no_candidates():
    with patch('src.downloader.os.makedirs'), \
         patch('src.downloader.subprocess.run'), \
         patch('glob.glob', return_value=[]), \
         patch('src.downloader.os.path.exists', return_value=False), \
         patch('src.downloader.open', mock_open()):
        out = downloader.download_captions('http://fake.url/vid', 'output/fake.vtt', 'en')
        assert out is None

# --- extract_captions_text ---
def test_extract_captions_text_success():
    fake_caption = MagicMock()
    fake_caption.text = "<b>Hello</b> world!"
    with patch('src.downloader.os.makedirs'), \
         patch('src.downloader.open', mock_open()), \
         patch('webvtt.read', return_value=[fake_caption]):
        out = downloader.extract_captions_text('file.vtt')
        assert "Hello" in out

def test_extract_captions_text_empty():
    with patch('src.downloader.os.makedirs'), \
         patch('src.downloader.open', mock_open()), \
         patch('webvtt.read', return_value=[]):
        out = downloader.extract_captions_text('file.vtt')
        assert out == ""

# --- extract_aligned_captions ---
def test_extract_aligned_captions_success():
    class FakeCaption:
        text = "<b>Hi there, this is real speech.</b>"
        start_in_seconds = 2.0
        end_in_seconds = 5.0
    fake_caption = FakeCaption()
    with patch('src.downloader.os.makedirs'), \
         patch('src.downloader.open', mock_open()), \
         patch('webvtt.read', return_value=[fake_caption]):
        out = downloader.extract_aligned_captions('file.vtt', (1, 10))
        assert "Hi" in out

def test_extract_aligned_captions_nomatch():
    fake_caption = MagicMock()
    fake_caption.text = "Nothing"
    fake_caption.start_in_seconds = 12
    fake_caption.end_in_seconds = 15
    with patch('src.downloader.os.makedirs'), \
         patch('src.downloader.open', mock_open()), \
         patch('webvtt.read', return_value=[fake_caption]):
        with pytest.raises(Exception):
            downloader.extract_aligned_captions('file.vtt', (1, 10))

