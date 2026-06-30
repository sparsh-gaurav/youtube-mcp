from unittest.mock import MagicMock

import pytest

from youtube_mcp.models import WhisperSegment, WhisperTranscript
from youtube_mcp.whisper import WhisperTranscriber

_FAKE_AUDIO = "/tmp/fake_dir/audio.webm"
_FAKE_DIR = "/tmp/fake_dir"


def _make_model(text="Hello world", segments=None, language="en"):
    if segments is None:
        segments = [{"start": 0.0, "end": 2.5, "text": "Hello world"}]
    model = MagicMock()
    model.transcribe.return_value = {"text": text, "segments": segments, "language": language}
    return model


def _make_transcriber(model=None):
    t = WhisperTranscriber()
    t._model = model or _make_model()
    t._ffmpeg_ready = True
    return t


def _patch_io(mocker, returncode=0):
    mocker.patch("tempfile.mkdtemp", return_value=_FAKE_DIR)
    mocker.patch("subprocess.run", return_value=MagicMock(returncode=returncode))
    mocker.patch("youtube_mcp.whisper.glob.glob", side_effect=lambda p: (
        [_FAKE_AUDIO] if "audio.*" in p else []
    ))
    mocker.patch("os.remove")
    mocker.patch("os.rmdir")


@pytest.fixture
def transcriber():
    return _make_transcriber()


def test_transcribe_happy_path(transcriber, mocker):
    _patch_io(mocker)

    result = transcriber.transcribe("dQw4w9WgXcQ")

    assert isinstance(result, WhisperTranscript)
    assert result.video_id == "dQw4w9WgXcQ"
    assert result.text == "Hello world"
    assert len(result.segments) == 1
    assert isinstance(result.segments[0], WhisperSegment)
    assert result.segments[0].start == 0.0
    assert result.segments[0].end == 2.5
    assert result.language_code == "en"


def test_transcribe_language_forwarded(mocker):
    model = _make_model()
    transcriber = _make_transcriber(model)
    _patch_io(mocker)

    transcriber.transcribe("dQw4w9WgXcQ", language="fr")

    call_kwargs = model.transcribe.call_args[1]
    assert call_kwargs.get("language") == "fr"


def test_transcribe_no_language_kwarg_when_none(mocker):
    model = _make_model()
    transcriber = _make_transcriber(model)
    _patch_io(mocker)

    transcriber.transcribe("dQw4w9WgXcQ")

    call_kwargs = model.transcribe.call_args[1]
    assert "language" not in call_kwargs


def test_transcribe_ytdlp_failure_raises(transcriber, mocker):
    _patch_io(mocker, returncode=1)

    with pytest.raises(ValueError, match="Failed to download audio for: dQw4w9WgXcQ"):
        transcriber.transcribe("dQw4w9WgXcQ")


def test_transcribe_whisper_error_raises(mocker):
    model = MagicMock()
    model.transcribe.side_effect = RuntimeError("model error")
    transcriber = _make_transcriber(model)
    _patch_io(mocker)

    with pytest.raises(ValueError, match="Transcription failed for: dQw4w9WgXcQ"):
        transcriber.transcribe("dQw4w9WgXcQ")


def test_transcribe_tempfile_cleaned_up_on_success(mocker):
    transcriber = _make_transcriber()
    _patch_io(mocker)
    mock_rmdir = mocker.patch("os.rmdir")

    transcriber.transcribe("dQw4w9WgXcQ")

    mock_rmdir.assert_called_once_with(_FAKE_DIR)


def test_transcribe_tempfile_cleaned_up_on_failure(mocker):
    model = MagicMock()
    model.transcribe.side_effect = RuntimeError("boom")
    transcriber = _make_transcriber(model)
    _patch_io(mocker)
    mock_rmdir = mocker.patch("os.rmdir")

    with pytest.raises(ValueError):
        transcriber.transcribe("dQw4w9WgXcQ")

    mock_rmdir.assert_called_once_with(_FAKE_DIR)
