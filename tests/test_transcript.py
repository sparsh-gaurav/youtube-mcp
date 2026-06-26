import pytest
from youtube_transcript_api import NoTranscriptFound, TranscriptsDisabled

from youtube_mcp.models import TranscriptSegment
from youtube_mcp.transcript import TranscriptFetcher

_MOCK_DATA = [
    {"start": 0.0, "duration": 2.5, "text": "Never gonna give you up"},
    {"start": 2.5, "duration": 2.0, "text": "Never gonna let you down"},
]


@pytest.fixture
def fetcher():
    return TranscriptFetcher()


def test_get_transcript_happy_path(fetcher, mocker):
    mocker.patch("youtube_mcp.transcript.YouTubeTranscriptApi.get_transcript", return_value=_MOCK_DATA)

    result = fetcher.get_transcript("dQw4w9WgXcQ")

    assert len(result) == 2
    assert all(isinstance(s, TranscriptSegment) for s in result)
    assert result[0].text == "Never gonna give you up"
    assert result[0].start == 0.0
    assert result[1].duration == 2.0


def test_get_transcript_with_language(fetcher, mocker):
    mock_get = mocker.patch(
        "youtube_mcp.transcript.YouTubeTranscriptApi.get_transcript",
        return_value=_MOCK_DATA,
    )
    fetcher.get_transcript("dQw4w9WgXcQ", language="en")
    mock_get.assert_called_once_with("dQw4w9WgXcQ", languages=["en"])


def test_get_transcript_transcripts_disabled(fetcher, mocker):
    mocker.patch(
        "youtube_mcp.transcript.YouTubeTranscriptApi.get_transcript",
        side_effect=TranscriptsDisabled("dQw4w9WgXcQ"),
    )
    with pytest.raises(ValueError, match="No transcript available for: dQw4w9WgXcQ"):
        fetcher.get_transcript("dQw4w9WgXcQ")


def test_get_transcript_no_transcript_found(fetcher, mocker):
    mocker.patch(
        "youtube_mcp.transcript.YouTubeTranscriptApi.get_transcript",
        side_effect=NoTranscriptFound("vid", ["en"], {}),
    )
    with pytest.raises(ValueError, match="No transcript available for: vid"):
        fetcher.get_transcript("vid")
