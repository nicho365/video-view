import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Tuple
from config import MAX_VIDEO_SIZE_MB


class MediaIngestError(Exception):
    """Dilempar saat input video tidak valid atau gagal diunduh dari URL."""


def create_temp_workspace() -> Path:
    """Membuat folder temporer unik untuk satu kali proses analisis video."""
    return Path(tempfile.mkdtemp(prefix="vid_analyzer_"))


def cleanup_workspace(workspace_dir: Optional[Path]) -> None:
    """Menghapus folder dan seluruh file sementara setelah proses selesai."""
    if workspace_dir and workspace_dir.exists():
        shutil.rmtree(workspace_dir, ignore_errors=True)


def validate_video_file(file_path: str) -> Path:
    """Memvalidasi keberadaan, ekstensi, dan batas ukuran file video lokal."""
    path = Path(file_path)
    if not path.exists() or not path.is_file():
        raise MediaIngestError("File video tidak ditemukan.")

    if path.suffix.lower() not in {".mp4", ".mov", ".webm", ".mkv"}:
        raise MediaIngestError(
            f"Format '{path.suffix}' belum didukung. Gunakan file .mp4."
        )

    size_mb = path.stat().st_size / (1024 * 1024)
    if size_mb > MAX_VIDEO_SIZE_MB:
        raise MediaIngestError(
            f"Ukuran video ({size_mb:.1f} MB) melebihi batas maksimum {MAX_VIDEO_SIZE_MB} MB. "
            "Silakan kompres atau potong video pendeknya terlebih dahulu."
        )

    return path


def resolve_video_input(
    uploaded_file_path: Optional[str],
    post_url: Optional[str],
    workspace_dir: Path,
) -> Tuple[Path, str]:
    """
    Menentukan sumber video:
    - Prioritas utama: file upload lokal (.mp4)
    - Fitur pelengkap: coba unduh via yt-dlp jika URL diberikan
    Mengembalikan (path_video_lokal, sumber_label).
    """
    if uploaded_file_path:
        validated = validate_video_file(uploaded_file_path)
        return validated, "upload_file"

    clean_url = (post_url or "").strip()
    if not clean_url:
        raise MediaIngestError(
            "Silakan unggah file video (.mp4) atau masukkan tautan postingan video."
        )

    if not clean_url.startswith(("http://", "https://")):
        raise MediaIngestError("Format URL tidak valid. Pastikan diawali http:// atau https://.")

    output_template = str(workspace_dir / "downloaded_video.%(ext)s")
    cmd = [
        "yt-dlp",
        "--no-playlist",
        "--merge-output-format",
        "mp4",
        "-f",
        "mp4/best[ext=mp4]/best",
        "-o",
        output_template,
        clean_url,
    ]

    try:
        subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=60,
        )
    except FileNotFoundError as exc:
        raise MediaIngestError(
            "yt-dlp belum terpasang di lingkungan aplikasi. "
            "Silakan unduh videonya lalu unggah file .mp4 secara langsung."
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise MediaIngestError(
            "Proses pengambilan video dari URL terlalu lama (timeout). "
            "Silakan unggah file .mp4 secara langsung."
        ) from exc
    except subprocess.CalledProcessError as exc:
        stderr_snippet = (exc.stderr or "").strip().splitlines()
        reason = stderr_snippet[-1] if stderr_snippet else "Akses ditolak atau format tidak didukung."
        raise MediaIngestError(
            f"Gagal mengambil video dari URL ({reason}). "
            "Konten media sosial mungkin privat, butuh login, atau memblokir IP server cloud. "
            "Silakan unduh videonya lalu unggah file .mp4 secara langsung."
        ) from exc

    downloaded_files = list(workspace_dir.glob("downloaded_video.*"))
    if not downloaded_files:
        raise MediaIngestError(
            "Video tidak berhasil disimpan dari URL. Silakan unggah file .mp4 secara langsung."
        )

    return validate_video_file(str(downloaded_files[0])), "url_download"
