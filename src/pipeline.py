from typing import Optional
from config import DEFAULT_KEYFRAMES
from src.ai_detector import detect_ai_content
from src.media_ingest import (
    MediaIngestError,
    cleanup_workspace,
    create_temp_workspace,
    resolve_video_input,
)
from src.model1_extractor import extract_raw_context
from src.model2_analyzer import analyze_video_information
from src.video_processor import extract_audio_track, extract_keyframes


def run_video_analysis_pipeline(
    uploaded_file_path: Optional[str] = None,
    post_url: Optional[str] = None,
    enable_ai_check: bool = False,
    transcript: str = "",
) -> dict:
    """
    Menjalankan pipeline lengkap:
    - Input (.mp4 utama / URL opsional)
    - Ekstraksi keyframe & audio
    - Deteksi AI opsional (status AI / Bukan AI)
    - Chaining langsung Model 1 -> Model 2 (hasil Model 1 tidak dikembalikan ke UI)
    - Pembersihan file sementara otomatis
    """
    workspace_dir = create_temp_workspace()
    try:
        video_path, source_type = resolve_video_input(
            uploaded_file_path=uploaded_file_path,
            post_url=post_url,
            workspace_dir=workspace_dir,
        )

        frames_dir = workspace_dir / "frames"
        audio_dir = workspace_dir / "audio"

        frame_paths = extract_keyframes(
            video_path=video_path,
            output_dir=frames_dir,
            num_frames=DEFAULT_KEYFRAMES,
        )
        _audio_path = extract_audio_track(
            video_path=video_path,
            output_dir=audio_dir,
        )
        # Catatan: jika nanti kamu menambahkan modul ASR (Whisper) untuk mengisi `transcript`
        # dari `_audio_path`, cukup isi variabel `transcript` di tahap ini sebelum ke Model 1.

        # 1. Deteksi AI opsional (hanya status indikasi, tanpa skor detail)
        ai_result = detect_ai_content(
            frame_paths=frame_paths,
            enabled=enable_ai_check,
        )

        # 2. Model 1: ekstraksi mentah ke variabel internal (tidak ditampilkan di UI)
        model1_out = extract_raw_context(
            transcript=transcript,
            frame_paths=frame_paths,
        )

        # 3. Chaining langsung dari Model 1 ke Model 2 untuk analisis mendalam
        model2_out = analyze_video_information(
            raw_notes=model1_out["raw_notes"],
            transcript=transcript,
        )

        return {
            "ok": True,
            "source_type": source_type,
            "ai_status": ai_result["status"],
            "ai_note": ai_result["note"],
            "ai_check_enabled": ai_result["enabled"],
            "analysis": model2_out["analysis"],
            "model1_used": model1_out["used_model"],
            "model2_used": model2_out["used_model"],
            "fallback_used": model1_out["is_fallback"] or model2_out["is_fallback"],
        }

    except MediaIngestError as exc:
        return {
            "ok": False,
            "error": str(exc),
        }
    except Exception as exc:
        return {
            "ok": False,
            "error": f"Terjadi kendala saat memproses video: {exc}",
        }
    finally:
        cleanup_workspace(workspace_dir)
