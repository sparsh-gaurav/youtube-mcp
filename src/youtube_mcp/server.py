import os
from typing import Literal

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from .api import YouTubeAPI
from .models import Transcript, TranscriptSegment, VideoMetadata, VideoSearchResult
from .sarvam import SarvamTranscriber
from .transcript import TranscriptFetcher
from .whisper import WhisperTranscriber

load_dotenv()

_api_key = os.environ.get("YOUTUBE_API_KEY")
if not _api_key:
    raise RuntimeError("YOUTUBE_API_KEY not set — copy .env.example to .env and add your key")

_youtube = YouTubeAPI(_api_key)
_transcript = TranscriptFetcher()
_whisper = WhisperTranscriber("base")
_sarvam_api_key = os.environ.get("SARVAM_API_KEY")
_sarvam = SarvamTranscriber(_sarvam_api_key) if _sarvam_api_key else None

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


@mcp.tool()
def search_videos(
    query: str,
    max_results: int = 5,
    language: str | None = None,
    order: str = "date",
) -> list[VideoSearchResult]:
    """Search YouTube videos by keyword, newest first.

    Args:
        query: Search query string.
        max_results: Number of results to return (1–50, default 5).
        language: BCP-47 language hint for results (e.g. 'en', 'ur'). Optional.
        order: Sort order — date (default), relevance, viewCount, rating.
    """
    return _youtube.search_videos(query, max_results, language, order)


@mcp.tool()
def transcribe_video(
    video_id: str,
    language: str | None = None,
    provider: Literal["whisper", "sarvam"] = "whisper",
) -> Transcript:
    """Download audio and transcribe a YouTube video. Works even when YouTube captions are unavailable.

    Args:
        video_id: YouTube video ID.
        language: BCP-47 language code hint (e.g. 'en', 'hi'). Auto-detected if omitted.
        provider: "whisper" (default) runs locally, no API key required. "sarvam" uses
            Sarvam AI's Saaras API — strong for Indian languages, requires SARVAM_API_KEY,
            and caps audio at 30 seconds (use "whisper" for longer videos).
    """
    if provider == "sarvam":
        if _sarvam is None:
            raise RuntimeError("SARVAM_API_KEY not set — copy .env.example to .env and add your key")
        result = _sarvam.transcribe(video_id, language)
        return Transcript(
            video_id=result.video_id,
            provider="sarvam",
            text=result.text,
            language_code=result.language_code,
        )

    result = _whisper.transcribe(video_id, language)
    return Transcript(
        video_id=result.video_id,
        provider="whisper",
        text=result.text,
        segments=result.segments,
    )


if __name__ == "__main__":
    mcp.run()
