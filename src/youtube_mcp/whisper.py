import glob
import os
import subprocess
import tempfile
from typing import Any


from .models import WhisperSegment, WhisperTranscript


class WhisperTranscriber:
    def __init__(self, model_name: str = "base") -> None:
        self._model_name = model_name
        self._model: Any = None
        self._ffmpeg_ready = False

    def _ensure_ready(self) -> None:
        if not self._ffmpeg_ready:
            import static_ffmpeg
            static_ffmpeg.add_paths()
            self._ffmpeg_ready = True
        if self._model is None:
            import whisper
            self._model = whisper.load_model(self._model_name)

    def transcribe(self, video_id: str, language: str | None = None) -> WhisperTranscript:
        self._ensure_ready()
        url = f"https://www.youtube.com/watch?v={video_id}"
        tmp_dir = tempfile.mkdtemp()
        try:
            result = subprocess.run(
                ["yt-dlp", "-x", "-o", os.path.join(tmp_dir, "audio.%(ext)s"), url],
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                raise ValueError(f"Failed to download audio for: {video_id}")

            matches = glob.glob(os.path.join(tmp_dir, "audio.*"))
            if not matches:
                raise ValueError(f"Failed to download audio for: {video_id}")
            audio_path = matches[0]

            kwargs: dict[str, Any] = {}
            if language:
                kwargs["language"] = language
            try:
                output = self._model.transcribe(audio_path, **kwargs)
            except Exception as exc:
                raise ValueError(f"Transcription failed for: {video_id}") from exc

            segments = [
                WhisperSegment(start=s["start"], end=s["end"], text=s["text"])
                for s in output.get("segments", [])
            ]
            return WhisperTranscript(
                video_id=video_id,
                text=output["text"],
                segments=segments,
            )
        finally:
            for f in glob.glob(os.path.join(tmp_dir, "*")):
                os.remove(f)
            os.rmdir(tmp_dir)
