# Social Media Video Analyzer & AI Content Indicator

Aplikasi web berbasis **Gradio** yang dirancang untuk di-deploy di **Hugging Face Spaces** (dengan *source code* dikelola di **GitHub**) guna menganalisis video pendek media sosial—baik untuk mengekstrak informasi konten secara mendalam maupun memeriksa secara opsional apakah video berindikasi konten AI.

## Fitur Utama
1. **Input Video (.mp4 Utama & URL Opsional):** Mendukung unggah file video pendek (`.mp4` disarankan) sebagai jalur utama serta percobaan unduh via `yt-dlp` untuk tautan postingan (dengan *fallback* jelas ke *upload* manual jika URL diblokir/privat).
2. **Ekstraksi Audio, Keyframe & Transkripsi:** Mengambil *keyframe* merata dengan resolusi ternormalisasi serta mengekstrak trek audio untuk ditranskripsi ke teks.
3. **Deteksi Konten AI Opsional:** Fitur opsional yang dapat diaktifkan saat dibutuhkan untuk memberikan indikasi awal (`Terindikasi AI` / `Tidak Terindikasi AI`) tanpa angka skor detail.
4. **Chaining Langsung Model 1 → Model 2:**
   - **Model 1 (Internal):** Menggabungkan transkrip audio dan catatan visual/*teks layar* menjadi catatan mentah di variabel internal (tidak ditampilkan di UI utama).
   - **Model 2 (Output Utama):** Mengolah hasil Model 1 menjadi informasi terstruktur dan mendalam.
5. **Automatic Model Fallback & Auto-Cleanup:** Berpindah otomatis ke model cadangan / mode *keyframe* lebih sedikit jika terkena batas *rate limit*, *token limit*, atau kuota *free tier*, serta menghapus file sementara setelah proses selesai.

## Menjalankan Secara Lokal
1. Clone repositori ini lalu masuk ke folder proyek.
2. Salin `.env.example` menjadi `.env` dan isi `OPENROUTER_API_KEY` (serta `GROQ_API_KEY` jika mengaktifkan transkripsi audio).
3. Install dependensi:
   ```bash
   pip install -r requirements.txt
