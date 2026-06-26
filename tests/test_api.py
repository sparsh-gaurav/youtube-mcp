import pytest

from youtube_mcp.api import YouTubeAPI
from youtube_mcp.models import VideoMetadata, VideoSearchResult

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


_MOCK_SEARCH_RESPONSE = {
    "items": [
        {
            "id": {"videoId": "abc123"},
            "snippet": {
                "title": "Ram Mandir Scam",
                "description": "News about the scam",
                "channelTitle": "NewsChannel",
                "publishedAt": "2026-06-20T10:00:00Z",
                "thumbnails": {"default": {"url": "https://i.ytimg.com/vi/abc123/default.jpg"}},
            },
        },
        {
            "id": {"videoId": "def456"},
            "snippet": {
                "title": "Ram Mandir Update",
                "description": "Latest update",
                "channelTitle": "AnotherChannel",
                "publishedAt": "2026-06-21T10:00:00Z",
                "thumbnails": {"default": {"url": "https://i.ytimg.com/vi/def456/default.jpg"}},
            },
        },
    ]
}


def _make_search_api(mocker, response):
    mock_build = mocker.patch("youtube_mcp.api.build")
    mock_service = mock_build.return_value
    mock_service.search.return_value.list.return_value.execute.return_value = response
    return YouTubeAPI("fake-key")


def test_search_videos_returns_results(mocker):
    api = _make_search_api(mocker, _MOCK_SEARCH_RESPONSE)
    results = api.search_videos("Ram Mandir scam")

    assert len(results) == 2
    assert all(isinstance(r, VideoSearchResult) for r in results)
    assert results[0].video_id == "abc123"
    assert results[0].title == "Ram Mandir Scam"
    assert results[1].video_id == "def456"


def test_search_videos_passes_params(mocker):
    mock_build = mocker.patch("youtube_mcp.api.build")
    mock_service = mock_build.return_value
    mock_service.search.return_value.list.return_value.execute.return_value = {"items": []}
    api = YouTubeAPI("fake-key")

    api.search_videos("test query", max_results=5, language="ur", order="date")

    mock_service.search.return_value.list.assert_called_once_with(
        part="snippet",
        q="test query",
        type="video",
        maxResults=5,
        order="date",
        relevanceLanguage="ur",
    )


def test_search_videos_empty_results(mocker):
    api = _make_search_api(mocker, {"items": []})
    assert api.search_videos("nothing") == []


def test_search_videos_skips_non_video_items(mocker):
    response = {
        "items": [
            {"id": {"playlistId": "PL123"}, "snippet": {}},  # playlist item, no videoId
            _MOCK_SEARCH_RESPONSE["items"][0],
        ]
    }
    api = _make_search_api(mocker, response)
    results = api.search_videos("test")
    assert len(results) == 1
    assert results[0].video_id == "abc123"


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
