import base64
from pathlib import Path
from typing import List
import requests
from config import (
    FALLBACK_KEYFRAMES,
    MODEL1_CANDIDATES,
    OPENROUTER_API_KEY,
    OPENROUTER_BASE_URL,
    REQUEST_TIMEOUT_SECONDS,
)


class QuotaOrRateLimitError(Exception):
    """Dilempar saat model terkena limit token, rate limit (429), atau kuota habis."""


def _encode_image_base64(image_path: str) -> str:
    data = Path(image_path).read_bytes()
    return base64.b64encode(data).decode("utf-8")


def _call_vision_model(
    model_name: str,
    transcript: str,
    frame_paths: List[str],
) -> str:
    if not OPENROUTER_API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY belum diatur.")

    prompt_text = (
        "Tugasmu adalah mencatat informasi faktual dari video pendek media sosial.\n"
        "1. Catat adegan utama, objek, dan seluruh teks/tulisan yang muncul di layar pada gambar-gambar ini.\n"
        "2. Gabungkan konteksnya dengan transkrip audio berikut (jika ada).\n"
        "3. Jangan menyimpulkan atau merangkum panjang—cukup tulis catatan faktual yang jelas dan padat.\n\n"
        f"Transkrip Audio:\n{transcript.strip() if transcript else '(Tidak ada dialog/narasi suara)'}"
    )

    content = [{"type": "text", "text": prompt_text}]
    for img_path in frame_paths:
        b64 = _encode_image_base64(img_path)
        content.append(
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{b64}"},
            }
        )

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model_name,
        "messages": [{"role": "user", "content": content}],
        "max_tokens": 700,
    }

    resp = requests.post(
        OPENROUTER_BASE_URL,
        headers=headers,
        json=payload,
        timeout=REQUEST_TIMEOUT_SECONDS,
    )

    if resp.status_code in (402, 429, 502, 503, 504):
        raise QuotaOrRateLimitError(f"Model {model_name} gagal ({resp.status_code}): {resp.text[:200]}")

    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"].strip()


def extract_raw_context(
    transcript: str,
    frame_paths: List[str],
) -> dict:
    """
    Menghasilkan catatan mentah dari audio + visual dengan fallback otomatis.
    Output ini dirancang untuk langsung diteruskan ke Model 2 (tidak perlu tampil di UI).
    """
    # Coba dengan jumlah frame penuh dulu, lalu mode hemat frame jika masih kena limit
    frame_sets = [frame_paths]
    if len(frame_paths) > FALLBACK_KEYFRAMES:
        frame_sets.append(frame_paths[:FALLBACK_KEYFRAMES])

    last_error = None
    for idx_set, frames in enumerate(frame_sets):
        for model_name in MODEL1_CANDIDATES:
            try:
                raw_notes = _call_vision_model(model_name, transcript, frames)
                return {
                    "raw_notes": raw_notes,
                    "used_model": model_name,
                    "frames_used": len(frames),
                    "is_fallback": idx_set > 0 or model_name != MODEL1_CANDIDATES[0],
                }
            except QuotaOrRateLimitError as exc:
                last_error = exc
                continue
            except Exception as exc:
                last_error = exc
                continue

    # Fallback terakhir: pakai transkrip audio saja tanpa gambar jika semua panggilan vision gagal
    fallback_text = (
        f"Transkrip Audio:\n{transcript.strip() if transcript else '(Tidak tersedia)'}\n"
        f"Catatan Visual: Gagal mengambil deskripsi gambar ({last_error})."
    )
    return {
        "raw_notes": fallback_text,
        "used_model": "transcript-only-fallback",
        "frames_used": 0,
        "is_fallback": True,
    }
