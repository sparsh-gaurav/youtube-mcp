from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import CouldNotRetrieveTranscript

from .models import TranscriptSegment


class TranscriptFetcher:
    def __init__(self) -> None:
        self._api = YouTubeTranscriptApi()

    def get_transcript(self, video_id: str, language: str | None = None) -> list[TranscriptSegment]:
        try:
            if language:
                snippets = self._api.fetch(video_id, languages=[language])
            else:
                # pick first available language rather than defaulting to 'en'
                transcript_list = self._api.list(video_id)
                first = next(iter(transcript_list))
                snippets = first.fetch()
        except CouldNotRetrieveTranscript:
            raise ValueError(f"No transcript available for: {video_id}")

        return [
            TranscriptSegment(start=s.start, duration=s.duration, text=s.text)
            for s in snippets
        ]
