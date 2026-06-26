import os

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from .api import YouTubeAPI
from .models import TranscriptSegment, VideoMetadata
from .transcript import TranscriptFetcher

load_dotenv()

_api_key = os.environ.get("YOUTUBE_API_KEY")
if not _api_key:
    raise RuntimeError("YOUTUBE_API_KEY not set — copy .env.example to .env and add your key")

_youtube = YouTubeAPI(_api_key)
_transcript = TranscriptFetcher()

mcp = FastMCP("youtube")


@mcp.tool()
def get_video(video_id: str) -> VideoMetadata:
    """Fetch metadata for a YouTube video by its ID (e.g. dQw4w9WgXcQ)."""
    return _youtube.get_video(video_id)


@mcp.tool()
def get_transcript(video_id: str, language: str | None = None) -> list[TranscriptSegment]:
    """Fetch timestamped transcript segments for a YouTube video.

    Args:
        video_id: YouTube video ID.
        language: BCP-47 language code (e.g. 'en', 'fr'). Defaults to first available.
    """
    return _transcript.get_transcript(video_id, language)


if __name__ == "__main__":
    mcp.run()
