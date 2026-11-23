import requests
from config import (
    MODEL2_CANDIDATES,
    OPENROUTER_API_KEY,
    OPENROUTER_BASE_URL,
    REQUEST_TIMEOUT_SECONDS,
)


class Model2LimitError(Exception):
    """Dilempar saat model analisis terkena rate limit / token limit / error sementara."""


def _call_text_model(model_name: str, system_prompt: str, user_prompt: str) -> str:
    if not OPENROUTER_API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY belum diatur.")

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "max_tokens": 1200,
    }

    resp = requests.post(
        OPENROUTER_BASE_URL,
        headers=headers,
        json=payload,
        timeout=REQUEST_TIMEOUT_SECONDS,
    )

    if resp.status_code in (402, 429, 502, 503, 504):
        raise Model2LimitError(f"Model {model_name} gagal ({resp.status_code}): {resp.text[:200]}")

    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"].strip()


def analyze_video_information(raw_notes: str, transcript: str = "") -> dict:
    """
    Menerima hasil Model 1 secara langsung dan menghasilkan informasi mendalam
    yang siap ditampilkan di UI aplikasi.
    """
    # Pangkas input jika sangat panjang agar aman terhadap batas token model cadangan
    trimmed_notes = raw_notes[:6000]
    trimmed_transcript = transcript[:3000]

    system_prompt = (
        "Kamu adalah asisten analis konten video media sosial. "
        "Tugasmu mengolah data mentah dari video (catatan visual, teks layar, dan audio) "
        "menjadi informasi yang jelas, terstruktur, dan mendalam dalam Bahasa Indonesia. "
        "Jangan mengarang fakta yang tidak ada di data."
    )

    user_prompt = (
        "Berdasarkan data hasil ekstraksi video berikut, susun informasi yang lengkap dan rapi:\n"
        "1. **Ringkasan Inti & Topik Utama**\n"
        "2. **Poin Informasi / Klaim / Langkah Penting**\n"
        "3. **Entitas atau Detail Spesifik** (produk, tempat, istilah, angka, atau teks layar yang relevan)\n"
        "4. **Catatan Konteks & Kejelasan Informasi** (apakah ada informasi yang kurang jelas/terpotong)\n\n"
        f"--- CATATAN EKSTRAKSI MODEL 1 ---\n{trimmed_notes}\n\n"
        f"--- TRANSKRIP AUDIO PENDUKUNG ---\n{trimmed_transcript or '(Tidak ada)'}"
    )

    last_error = None
    for idx, model_name in enumerate(MODEL2_CANDIDATES):
        try:
            result_text = _call_text_model(model_name, system_prompt, user_prompt)
            return {
                "analysis": result_text,
                "used_model": model_name,
                "is_fallback": idx > 0,
            }
        except Model2LimitError as exc:
            last_error = exc
            continue
        except Exception as exc:
            last_error = exc
            continue

    return {
        "analysis": (
            "Maaf, seluruh model analisis sedang mengalami batas kuota/request saat ini.\n\n"
            f"Detail teknis terakhir: {last_error}"
        ),
        "used_model": "none",
        "is_fallback": True,
    }
