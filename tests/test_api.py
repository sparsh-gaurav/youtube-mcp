import pytest

from youtube_mcp.api import YouTubeAPI
from youtube_mcp.models import VideoMetadata

_MOCK_RESPONSE = {
    "items": [
        {
            "id": "dQw4w9WgXcQ",
            "snippet": {
                "title": "Rick Astley - Never Gonna Give You Up",
                "description": "The official video.",
                "channelTitle": "Rick Astley",
                "publishedAt": "2009-10-25T06:57:33Z",
                "thumbnails": {"default": {"url": "https://i.ytimg.com/vi/dQw4w9WgXcQ/default.jpg"}},
            },
            "statistics": {"viewCount": "1000000000", "likeCount": "15000000"},
            "contentDetails": {"duration": "PT3M33S"},
        }
    ]
}


def _make_api(mocker, response):
    mock_build = mocker.patch("youtube_mcp.api.build")
    mock_service = mock_build.return_value
    mock_service.videos.return_value.list.return_value.execute.return_value = response
    return YouTubeAPI("fake-key")


def test_get_video_returns_metadata(mocker):
    api = _make_api(mocker, _MOCK_RESPONSE)
    result = api.get_video("dQw4w9WgXcQ")

    assert isinstance(result, VideoMetadata)
    assert result.id == "dQw4w9WgXcQ"
    assert result.title == "Rick Astley - Never Gonna Give You Up"
    assert result.channel_title == "Rick Astley"
    assert result.view_count == 1_000_000_000
    assert result.like_count == 15_000_000
    assert result.duration == "PT3M33S"
    assert result.published_at == "2009-10-25T06:57:33Z"


def test_get_video_not_found_raises(mocker):
    api = _make_api(mocker, {"items": []})
    with pytest.raises(ValueError, match="Video not found: badid"):
        api.get_video("badid")


def test_get_video_like_count_hidden(mocker):
    response = {
        "items": [
            {
                **_MOCK_RESPONSE["items"][0],
                "statistics": {"viewCount": "500"},  # likeCount absent (hidden by creator)
            }
        ]
    }
    api = _make_api(mocker, response)
    result = api.get_video("dQw4w9WgXcQ")
    assert result.like_count is None
    assert result.view_count == 500
