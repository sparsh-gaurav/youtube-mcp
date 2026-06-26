from youtube_transcript_api import NoTranscriptFound, TranscriptsDisabled, YouTubeTranscriptApi

from .models import TranscriptSegment


class TranscriptFetcher:
    def get_transcript(self, video_id: str, language: str | None = None) -> list[TranscriptSegment]:
        try:
            if language:
                data = YouTubeTranscriptApi.get_transcript(video_id, languages=[language])
            else:
                data = YouTubeTranscriptApi.get_transcript(video_id)
        except (TranscriptsDisabled, NoTranscriptFound):
            raise ValueError(f"No transcript available for: {video_id}")

        return [
            TranscriptSegment(start=s["start"], duration=s["duration"], text=s["text"])
            for s in data
        ]
