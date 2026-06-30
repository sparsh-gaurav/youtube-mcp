from unittest.mock import MagicMock, mock_open

import pytest

from youtube_mcp.models import SarvamTranscript
from youtube_mcp.sarvam import SarvamTranscriber

_FAKE_AUDIO = "/tmp/fake_dir/audio.webm"
_FAKE_DIR = "/tmp/fake_dir"


def _make_response(status_code=200, json_payload=None, text=""):
    response = MagicMock()
    response.status_code = status_code
    response.text = text
    response.json.return_value = json_payload or {}
    return response


def _patch_io(mocker, returncode=0):
    mocker.patch("tempfile.mkdtemp", return_value=_FAKE_DIR)
    mocker.patch("subprocess.run", return_value=MagicMock(returncode=returncode))
    mocker.patch("youtube_mcp.sarvam.glob.glob", side_effect=lambda p: (
        [_FAKE_AUDIO] if "audio.*" in p else []
    ))
    mocker.patch("builtins.open", mock_open(read_data=b"fake-audio-bytes"))
    mocker.patch("os.remove")
    mocker.patch("os.rmdir")


@pytest.fixture
def transcriber():
    return SarvamTranscriber("fake-api-key")


def test_transcribe_happy_path(transcriber, mocker):
    _patch_io(mocker)
    mock_post = mocker.patch(
        "youtube_mcp.sarvam.requests.post",
        return_value=_make_response(json_payload={"transcript": "Hello world", "language_code": "en-IN"}),
    )

    result = transcriber.transcribe("dQw4w9WgXcQ")

    assert isinstance(result, SarvamTranscript)
    assert result.video_id == "dQw4w9WgXcQ"
    assert result.text == "Hello world"
    assert result.language_code == "en-IN"
    assert mock_post.call_args[1]["headers"] == {"api-subscription-key": "fake-api-key"}
    filename, _file_obj, content_type = mock_post.call_args[1]["files"]["file"]
    assert filename == "audio.webm"
    assert content_type == "video/webm"


def test_transcribe_language_forwarded(transcriber, mocker):
    _patch_io(mocker)
    mock_post = mocker.patch(
        "youtube_mcp.sarvam.requests.post",
        return_value=_make_response(json_payload={"transcript": "Bonjour"}),
    )

    transcriber.transcribe("dQw4w9WgXcQ", language="fr")

    assert mock_post.call_args[1]["data"]["language_code"] == "fr"


def test_transcribe_no_language_key_when_none(transcriber, mocker):
    _patch_io(mocker)
    mock_post = mocker.patch(
        "youtube_mcp.sarvam.requests.post",
        return_value=_make_response(json_payload={"transcript": "Hello"}),
    )

    transcriber.transcribe("dQw4w9WgXcQ")

    assert "language_code" not in mock_post.call_args[1]["data"]


def test_transcribe_ytdlp_failure_raises(transcriber, mocker):
    _patch_io(mocker, returncode=1)

    with pytest.raises(ValueError, match="Failed to download audio for: dQw4w9WgXcQ"):
        transcriber.transcribe("dQw4w9WgXcQ")


def test_transcribe_api_error_raises(transcriber, mocker):
    _patch_io(mocker)
    mocker.patch(
        "youtube_mcp.sarvam.requests.post",
        return_value=_make_response(status_code=401, text="unauthorized"),
    )

    with pytest.raises(ValueError, match="Sarvam transcription failed for dQw4w9WgXcQ"):
        transcriber.transcribe("dQw4w9WgXcQ")


def test_transcribe_tempfile_cleaned_up_on_success(transcriber, mocker):
    _patch_io(mocker)
    mocker.patch(
        "youtube_mcp.sarvam.requests.post",
        return_value=_make_response(json_payload={"transcript": "Hello"}),
    )
    mock_rmdir = mocker.patch("os.rmdir")

    transcriber.transcribe("dQw4w9WgXcQ")

    mock_rmdir.assert_called_once_with(_FAKE_DIR)


def test_transcribe_tempfile_cleaned_up_on_failure(transcriber, mocker):
    _patch_io(mocker)
    mocker.patch(
        "youtube_mcp.sarvam.requests.post",
        return_value=_make_response(status_code=500, text="server error"),
    )
    mock_rmdir = mocker.patch("os.rmdir")

    with pytest.raises(ValueError):
        transcriber.transcribe("dQw4w9WgXcQ")

    mock_rmdir.assert_called_once_with(_FAKE_DIR)
