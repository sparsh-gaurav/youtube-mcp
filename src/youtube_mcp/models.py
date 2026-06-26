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
