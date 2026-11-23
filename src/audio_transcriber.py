from pathlib import Path
from typing import Optional, Tuple
import requests
from config import (
    ASR_MODEL_CANDIDATES,
    GROQ_API_KEY,
    GROQ_TRANSCRIPTION_URL,
    REQUEST_TIMEOUT_SECONDS,
)


def transcribe_audio_file(audio_path: Optional[str]) -> Tuple[str, str]:
    """
    Mengubah file audio (.wav) menjadi transkrip teks menggunakan API ASR
    dengan fallback otomatis antar kandidat model.
    Mengembalikan (transcript_text, status_label).
    """
    if not audio_path:
        return "", "no_audio"

    wav_file = Path(audio_path)
    if not wav_file.exists() or wav_file.stat().st_size == 0:
        return "", "empty_audio"

    if not GROQ_API_KEY:
        return "", "skipped_no_key"

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
    }

    for model_name in ASR_MODEL_CANDIDATES:
        try:
            with wav_file.open("rb") as f:
                files = {"file": (wav_file.name, f, "audio/wav")}
                data = {
                    "model": model_name,
                    "response_format": "text",
                }
                resp = requests.post(
                    GROQ_TRANSCRIPTION_URL,
                    headers=headers,
                    files=files,
                    data=data,
                    timeout=REQUEST_TIMEOUT_SECONDS,
                )

            if resp.status_code in (402, 429, 502, 503, 504):
                continue

            resp.raise_for_status()
            transcript = resp.text.strip()
            if transcript:
                return transcript, f"ok:{model_name}"
        except Exception:
            continue

    return "", "fallback_empty"
