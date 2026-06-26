# youtube-mcp

MCP server for YouTube. Exposes two tools to any MCP client (Claude Desktop, etc.):

- **`get_video`** — fetch video metadata (title, description, views, duration, etc.)
- **`get_transcript`** — fetch timestamped transcript/caption segments

## Setup

### 1. Get a YouTube Data API v3 key

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Create a project → **APIs & Services → Enable APIs** → search "YouTube Data API v3" → Enable
3. **APIs & Services → Credentials → Create Credentials → API Key**
4. Copy the key

### 2. Install

```bash
git clone https://github.com/your-username/youtube-mcp.git
cd youtube-mcp
pip install -e ".[dev]"
```

### 3. Configure

```bash
cp .env.example .env
# edit .env and paste your API key
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
      "command": "python",
      "args": ["-m", "youtube_mcp.server"],
      "cwd": "/path/to/youtube-mcp",
      "env": {
        "YOUTUBE_API_KEY": "your_key_here"
      }
    }
  }
}
```

Restart Claude Desktop. You can then ask Claude things like:

> "Get me the transcript for video dQw4w9WgXcQ"
> "What is the view count and duration of this YouTube video: ..."

## Tools

### `get_video(video_id: str) -> VideoMetadata`

| Field | Type | Description |
|---|---|---|
| `id` | str | YouTube video ID |
| `title` | str | Video title |
| `description` | str | Full description |
| `channel_title` | str | Channel name |
| `view_count` | int | Total views |
| `like_count` | int \| None | Likes (None if hidden) |
| `duration` | str | ISO 8601 duration (e.g. `PT3M33S`) |
| `published_at` | str | ISO 8601 publish date |
| `thumbnail_url` | str | Default thumbnail URL |

### `get_transcript(video_id: str, language: str | None = None) -> list[TranscriptSegment]`

| Field | Type | Description |
|---|---|---|
| `start` | float | Segment start time (seconds) |
| `duration` | float | Segment duration (seconds) |
| `text` | str | Caption text |

`language`: BCP-47 code (e.g. `"en"`, `"fr"`). Defaults to first available language.

## Project structure

```
src/youtube_mcp/
  server.py       # MCP entry point, tool registry
  api.py          # YouTube Data API v3 wrapper
  transcript.py   # youtube-transcript-api wrapper
  models.py       # Pydantic models
tests/
  test_api.py
  test_transcript.py
```
