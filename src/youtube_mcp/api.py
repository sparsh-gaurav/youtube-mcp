from googleapiclient.discovery import build

from .models import VideoMetadata, VideoSearchResult


class YouTubeAPI:
    def __init__(self, api_key: str) -> None:
        self._service = build("youtube", "v3", developerKey=api_key)

    def get_video(self, video_id: str) -> VideoMetadata:
        response = self._service.videos().list(
            part="snippet,statistics,contentDetails",
            id=video_id,
        ).execute()

        items = response.get("items", [])
        if not items:
            raise ValueError(f"Video not found: {video_id}")

        item = items[0]
        snippet = item["snippet"]
        stats = item.get("statistics", {})
        details = item["contentDetails"]

        return VideoMetadata(
            id=item["id"],
            title=snippet["title"],
            description=snippet.get("description", ""),
            channel_title=snippet["channelTitle"],
            view_count=int(stats.get("viewCount", 0)),
            like_count=int(stats["likeCount"]) if "likeCount" in stats else None,
            duration=details["duration"],
            published_at=snippet["publishedAt"],
            thumbnail_url=snippet["thumbnails"]["default"]["url"],
        )

    def search_videos(
        self,
        query: str,
        max_results: int = 10,
        language: str | None = None,
        order: str = "relevance",
    ) -> list[VideoSearchResult]:
        params: dict = {
            "part": "snippet",
            "q": query,
            "type": "video",
            "maxResults": min(max(1, max_results), 50),
            "order": order,
        }
        if language:
            params["relevanceLanguage"] = language

        response = self._service.search().list(**params).execute()

        results = []
        for item in response.get("items", []):
            video_id = item["id"].get("videoId")
            if not video_id:
                continue
            snippet = item["snippet"]
            results.append(VideoSearchResult(
                video_id=video_id,
                title=snippet["title"],
                description=snippet.get("description", ""),
                channel_title=snippet["channelTitle"],
                published_at=snippet["publishedAt"],
                thumbnail_url=snippet["thumbnails"]["default"]["url"],
            ))
        return results
