import glob
import mimetypes
import os
import subprocess
import tempfile

import requests

from .models import SarvamTranscript

SARVAM_STT_URL = "https://api.sarvam.ai/speech-to-text-translate"


class SarvamTranscriber:
    def __init__(self, api_key: str, model: str = "saaras:v2.5") -> None:
        self._api_key = api_key
        self._model = model

    def transcribe(self, video_id: str, language: str | None = None) -> SarvamTranscript:
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

            data = {"model": self._model}
            if language:
                data["language_code"] = language

            filename = os.path.basename(audio_path)
            content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
            with open(audio_path, "rb") as audio_file:
                response = requests.post(
                    SARVAM_STT_URL,
                    headers={"api-subscription-key": self._api_key},
                    data=data,
                    files={"file": (filename, audio_file, content_type)},
                    timeout=120,
                )

            if response.status_code != 200:
                raise ValueError(
                    f"Sarvam transcription failed for {video_id}: "
                    f"{response.status_code} {response.text}"
                )

            payload = response.json()
            return SarvamTranscript(
                video_id=video_id,
                text=payload.get("transcript", ""),
                language_code=payload.get("language_code"),
            )
        finally:
            for f in glob.glob(os.path.join(tmp_dir, "*")):
                os.remove(f)
            os.rmdir(tmp_dir)
