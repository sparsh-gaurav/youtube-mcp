# youtube-mcp

MCP server for YouTube. Exposes four tools to any MCP client (Claude Desktop, etc.):

| Tool | What it does |
|---|---|
| `get_video` | Fetch video metadata (title, views, duration, etc.) |
| `get_transcript` | Fetch timestamped caption segments (YouTube captions) |
| `search_videos` | Search YouTube by keyword, ordered by date or relevance |
| `transcribe_video` | Download audio and transcribe it — works when captions are unavailable. Defaults to local Whisper (no API key); pass `provider="sarvam"` to use Sarvam AI's Saaras API instead (`SARVAM_API_KEY` required) |

> **Zero system dependencies.** `ffmpeg` is bundled via `static-ffmpeg` and downloaded automatically on first use. No Homebrew, no manual installs.

## Setup

### 1. Get a YouTube Data API v3 key

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Create a project → **APIs & Services → Enable APIs** → search "YouTube Data API v3" → Enable
3. **APIs & Services → Credentials → Create Credentials → API Key**
4. Copy the key

### 2. Install

```bash
git clone https://github.com/sparsh-gaurav/youtube-mcp.git
cd youtube-mcp
pip install -e ".[dev]"
```

### 3. Configure

```bash
cp .env.example .env
# edit .env and paste your YOUTUBE_API_KEY
# optionally add SARVAM_API_KEY to enable provider="sarvam" in transcribe_video
```

### 4. Run tests

```bash
pytest -v
```

### 5. Wire up Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "youtube": {
      "command": "/path/to/youtube-mcp/.venv/bin/python3",
      "args": ["-m", "youtube_mcp.server"],
      "cwd": "/path/to/youtube-mcp",
      "env": {
        "YOUTUBE_API_KEY": "your_key_here"
      }
    }
  }
}
```

Restart Claude Desktop. You can then ask things like:

> "Search the latest YouTube videos about Ram Mandir fund scam and summarise them"  
> "Get the transcript for video dQw4w9WgXcQ"  
> "Transcribe this video even though it has no captions: ..."  
> "Transcribe this short Hindi clip using Sarvam: ..."  
> "What is the view count and duration of this YouTube video?"

## First-run notes

- **`transcribe_video` first call**: downloads the Whisper `base` model (~145 MB) to `~/.cache/whisper` and the bundled `ffmpeg` binary (~60 MB) to the Python package directory. Both are cached — subsequent calls are fast.
- **Temp files**: audio downloaded during transcription is stored in a system temp directory and deleted automatically after each call, whether it succeeds or fails.

## Tools

### `get_video(video_id: str) -> VideoMetadata`

| Field | Type | Description |
|---|---|---|
| `id` | str | YouTube video ID |
| `title` | str | Video title |
| `description` | str | Full description |
| `channel_title` | str | Channel name |
| `view_count` | int | Total views |
| `like_count` | int \| None | Likes (None if hidden by creator) |
| `duration` | str | ISO 8601 duration (e.g. `PT3M33S`) |
| `published_at` | str | ISO 8601 publish date |
| `thumbnail_url` | str | Default thumbnail URL |

---

### `get_transcript(video_id: str, language: str | None = None) -> list[TranscriptSegment]`

Returns YouTube's caption segments when available.

| Field | Type | Description |
|---|---|---|
| `start` | float | Segment start time (seconds) |
| `duration` | float | Segment duration (seconds) |
| `text` | str | Caption text |

`language`: BCP-47 code (e.g. `"en"`, `"hi"`). Defaults to first available language.

---

### `search_videos(query: str, max_results: int = 5, language: str | None = None, order: str = "date") -> list[VideoSearchResult]`

Searches YouTube via the Data API v3. Returns newest-first by default.

| Field | Type | Description |
|---|---|---|
| `video_id` | str | YouTube video ID |
| `title` | str | Video title |
| `description` | str | Snippet description |
| `channel_title` | str | Channel name |
| `published_at` | str | ISO 8601 publish date |
| `thumbnail_url` | str | Default thumbnail URL |

`max_results`: 1–50, default 5.  
`order`: `date` (default), `relevance`, `viewCount`, `rating`.  
`language`: BCP-47 relevance hint (e.g. `"en"`, `"hi"`). Optional.

---

### `transcribe_video(video_id: str, language: str | None = None, provider: Literal["whisper", "sarvam"] = "whisper") -> Transcript`

Downloads audio and transcribes it. Works even when YouTube captions are unavailable.

- `provider="whisper"` (default): runs locally via OpenAI Whisper (`base` model). No API key required.
- `provider="sarvam"`: uses Sarvam AI's Saaras speech-to-text API — strong for Indian languages. Requires `SARVAM_API_KEY`.

> **Sarvam 30-second limit.** Sarvam's synchronous Saaras API only accepts audio up to 30 seconds — longer videos return a 400 error. Use the default `provider="whisper"` for anything longer.

| Field | Type | Description |
|---|---|---|
| `video_id` | str | YouTube video ID |
| `provider` | str | Which backend produced this transcript (`"whisper"` or `"sarvam"`) |
| `text` | str | Full transcript text |
| `segments` | list[WhisperSegment] \| None | Timestamped segments (Whisper only; `None` for Sarvam) |
| `language_code` | str \| None | Detected/used language code (Sarvam only; `None` for Whisper) |

Each `WhisperSegment`:

| Field | Type | Description |
|---|---|---|
| `start` | float | Segment start time (seconds) |
| `end` | float | Segment end time (seconds) |
| `text` | str | Transcribed text |

`language`: BCP-47 hint (e.g. `"en"`, `"hi"`). Auto-detected if omitted.

---

## Project structure

```
src/youtube_mcp/
  server.py       # MCP entry point, tool registry
  api.py          # YouTube Data API v3 wrapper (get_video, search_videos)
  transcript.py   # youtube-transcript-api wrapper (get_transcript)
  whisper.py      # yt-dlp + local Whisper transcriber (transcribe_video, provider="whisper")
  sarvam.py       # yt-dlp + Sarvam Saaras API transcriber (transcribe_video, provider="sarvam")
  models.py       # Pydantic models
tests/
  test_api.py
  test_transcript.py
  test_whisper.py
  test_sarvam.py
```
