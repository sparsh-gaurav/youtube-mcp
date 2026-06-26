from googleapiclient.discovery import build

from .models import VideoMetadata


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
