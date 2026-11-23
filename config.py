import os

# Batas ukuran unggah video dalam MB (aman untuk video pendek medsos & container Space)
MAX_VIDEO_SIZE_MB = 35

# Jumlah keyframe standar vs. mode hemat token saat fallback
DEFAULT_KEYFRAMES = 5
FALLBACK_KEYFRAMES = 2
MAX_IMAGE_SIDE_PX = 768

# Endpoint & API Key (diisi lewat .env di lokal atau Secrets di Hugging Face Spaces)
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1/chat/completions"

# Groq API (opsional, untuk transkripsi audio Whisper cepat di cloud)
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_TRANSCRIPTION_URL = "https://api.groq.com/openai/v1/audio/transcriptions"
ASR_MODEL_CANDIDATES = [
    "whisper-large-v3-turbo",
    "distil-whisper-large-v3-en",
]

# Urutan model untuk Model 1 (Ekstraksi visual & teks layar -> deskripsi mentah)
# Ganti/sesuaikan dengan model multimodal/vision gratis yang aktif saat kamu deploy
MODEL1_CANDIDATES = [
    "qwen/qwen2.5-vl-32b-instruct:free",
    "meta-llama/llama-3.2-11b-vision-instruct:free",
    "google/gemma-3-27b-it:free",
]

# Urutan model untuk Model 2 (Analisis mendalam & sintesis informasi dari output Model 1)
MODEL2_CANDIDATES = [
    "deepseek/deepseek-r1-0528:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "mistralai/mistral-small-3.1-24b-instruct:free",
]

REQUEST_TIMEOUT_SECONDS = 45
