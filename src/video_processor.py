import subprocess
from pathlib import Path
from typing import List, Optional
import cv2
from PIL import Image
from config import MAX_IMAGE_SIDE_PX


def _resize_image_keep_aspect(image_path: Path, max_side: int) -> None:
    """Mengecilkan resolusi gambar jika sisi terpanjang melebihi max_side."""
    with Image.open(image_path) as img:
        img = img.convert("RGB")
        width, height = img.size
        longest = max(width, height)
        if longest > max_side:
            scale = max_side / float(longest)
            new_size = (max(1, int(width * scale)), max(1, int(height * scale)))
            img = img.resize(new_size, Image.Resampling.LANCZOS)
        img.save(image_path, format="JPEG", quality=82, optimize=True)


def extract_keyframes(
    video_path: Path,
    output_dir: Path,
    num_frames: int = 5,
) -> List[str]:
    """
    Mengambil sejumlah keyframe secara merata dari video .mp4
    dan menyimpannya sebagai file JPEG terkompresi ringan.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError("Tidak dapat membuka file video untuk ekstraksi frame.")

    try:
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total_frames <= 0:
            return []

        count = max(1, min(num_frames, total_frames))
        if count == 1:
            indices = [total_frames // 2]
        else:
            indices = sorted(
                {
                    min(total_frames - 1, int(round(i * (total_frames - 1) / (count - 1))))
                    for i in range(count)
                }
            )

        saved_paths: List[str] = []
        for idx, frame_idx in enumerate(indices):
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ok, frame = cap.read()
            if not ok or frame is None:
                continue

            frame_file = output_dir / f"keyframe_{idx + 1}.jpg"
            cv2.imwrite(str(frame_file), frame)
            _resize_image_keep_aspect(frame_file, MAX_IMAGE_SIDE_PX)
            saved_paths.append(str(frame_file))

        return saved_paths
    finally:
        cap.release()


def extract_audio_track(video_path: Path, output_dir: Path) -> Optional[str]:
    """
    Mengekstrak trek audio menjadi file WAV mono 16kHz (cocok untuk ASR/Whisper).
    Mengembalikan None jika video tidak memiliki trek audio.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    audio_path = output_dir / "audio_16k.wav"

    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(video_path),
        "-vn",
        "-ac",
        "1",
        "-ar",
        "16000",
        str(audio_path),
    ]

    try:
        subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=45,
        )
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return None

    if audio_path.exists() and audio_path.stat().st_size > 0:
        return str(audio_path)
    return None
