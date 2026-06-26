import pytest
from unittest.mock import MagicMock
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound

from youtube_mcp.models import TranscriptSegment
from youtube_mcp.transcript import TranscriptFetcher


def _make_snippet(start, duration, text):
    s = MagicMock()
    s.start = start
    s.duration = duration
    s.text = text
    return s


_MOCK_SNIPPETS = [
    _make_snippet(0.0, 2.5, "Never gonna give you up"),
    _make_snippet(2.5, 2.0, "Never gonna let you down"),
]


@pytest.fixture
def fetcher():
    return TranscriptFetcher()


def test_get_transcript_with_language(fetcher, mocker):
    mock_fetch = mocker.patch.object(fetcher._api, "fetch", return_value=_MOCK_SNIPPETS)

    result = fetcher.get_transcript("dQw4w9WgXcQ", language="en")

    mock_fetch.assert_called_once_with("dQw4w9WgXcQ", languages=["en"])
    assert len(result) == 2
    assert all(isinstance(s, TranscriptSegment) for s in result)
    assert result[0].text == "Never gonna give you up"
    assert result[0].start == 0.0
    assert result[1].duration == 2.0


def test_get_transcript_language_fallback(fetcher, mocker):
    mock_transcript = MagicMock()
    mock_transcript.fetch.return_value = _MOCK_SNIPPETS
    mock_list = mocker.patch.object(fetcher._api, "list", return_value=iter([mock_transcript]))

    result = fetcher.get_transcript("dQw4w9WgXcQ")

    mock_list.assert_called_once_with("dQw4w9WgXcQ")
    mock_transcript.fetch.assert_called_once()
    assert len(result) == 2


def test_get_transcript_transcripts_disabled(fetcher, mocker):
    mocker.patch.object(
        fetcher._api, "fetch", side_effect=TranscriptsDisabled("dQw4w9WgXcQ")
    )
    with pytest.raises(ValueError, match="No transcript available for: dQw4w9WgXcQ"):
        fetcher.get_transcript("dQw4w9WgXcQ", language="en")


def test_get_transcript_no_transcript_found(fetcher, mocker):
    mocker.patch.object(
        fetcher._api, "fetch", side_effect=NoTranscriptFound("vid", ["en"], {})
    )
    with pytest.raises(ValueError, match="No transcript available for: vid"):
        fetcher.get_transcript("vid", language="en")
