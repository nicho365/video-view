from typing import Dict, List
from PIL import Image
import torch
from transformers import pipeline

# Contoh model klasifikasi gambar AI-generated di Hugging Face Hub
# Bisa diganti di config.py sesuai model yang paling pas saat pengujian
AI_DETECTOR_MODEL_ID = "umm-maybe/AI-image-detector"

_DETECTOR_PIPE = None


def _get_detector_pipeline():
    global _DETECTOR_PIPE
    if _DETECTOR_PIPE is None:
        device = 0 if torch.cuda.is_available() else -1
        _DETECTOR_PIPE = pipeline(
            "image-classification",
            model=AI_DETECTOR_MODEL_ID,
            device=device,
        )
    return _DETECTOR_PIPE


def detect_ai_content(frame_paths: List[str], enabled: bool = False) -> Dict[str, str]:
    """
    Fitur opsional untuk menentukan secara singkat apakah video berindikasi AI atau bukan.
    Tidak mengembalikan skor/persentase detail, cukup status indikasi + catatan singkat.
    """
    if not enabled:
        return {
            "enabled": False,
            "status": "Dinonaktifkan",
            "note": "Pemeriksaan indikasi AI tidak diaktifkan untuk video ini.",
        }

    if not frame_paths:
        return {
            "enabled": True,
            "status": "Tidak Dapat Dipastikan",
            "note": "Tidak ada frame yang dapat diperiksa.",
        }

    clf = _get_detector_pipeline()
    ai_hits = 0
    checked_frames = 0

    for img_path in frame_paths:
        try:
            with Image.open(img_path) as img:
                preds = clf(img.convert("RGB"))
            checked_frames += 1

            # Ambil label teratas lalu cek apakah mengarah ke konten buatan AI / sintetis
            top_label = str(preds[0]["label"]).lower() if preds else ""
            if any(k in top_label for k in ("ai", "artificial", "fake", "synthetic", "generated")):
                ai_hits += 1
        except Exception:
            continue

    if checked_frames == 0:
        return {
            "enabled": True,
            "status": "Tidak Dapat Dipastikan",
            "note": "Gagal memproses frame untuk deteksi AI.",
        }

    # Jika mayoritas/sebagian frame terdeteksi berlabel AI, tandai sebagai Terindikasi AI
    is_ai = ai_hits >= max(1, (checked_frames + 1) // 2)
    if is_ai:
        return {
            "enabled": True,
            "status": "Terindikasi AI",
            "note": (
                "Terdapat indikasi visual buatan/rekayasa AI pada frame video "
                "(indikasi awal, dapat dipengaruhi kompresi media sosial)."
            ),
        }

    return {
        "enabled": True,
        "status": "Tidak Terindikasi AI",
        "note": (
            "Tidak ditemukan indikasi visual AI yang menonjol pada frame sampel "
            "(hasil berupa indikasi awal, bukan jaminan mutlak)."
        ),
    }
