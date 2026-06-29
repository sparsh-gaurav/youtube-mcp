from pydantic import BaseModel


class VideoMetadata(BaseModel):
    id: str
    title: str
    description: str
    channel_title: str
    view_count: int
    like_count: int | None = None
    duration: str  # ISO 8601, e.g. PT4M33S
    published_at: str
    thumbnail_url: str


class TranscriptSegment(BaseModel):
    start: float
    duration: float
    text: str


class VideoSearchResult(BaseModel):
    video_id: str
    title: str
    description: str
    channel_title: str
    published_at: str
    thumbnail_url: str


class WhisperSegment(BaseModel):
    start: float
    end: float
    text: str


class WhisperTranscript(BaseModel):
    video_id: str
    text: str
    segments: list[WhisperSegment]


class SarvamTranscript(BaseModel):
    video_id: str
    text: str
    language_code: str | None = None


class Transcript(BaseModel):
    video_id: str
    provider: str
    text: str
    segments: list[WhisperSegment] | None = None
    language_code: str | None = None
