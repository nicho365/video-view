import gradio as gr
from config import MAX_VIDEO_SIZE_MB
from src.pipeline import run_video_analysis_pipeline


def handle_analyze(uploaded_video, post_url, enable_ai_check):
    result = run_video_analysis_pipeline(
        uploaded_file_path=uploaded_video,
        post_url=post_url,
        enable_ai_check=bool(enable_ai_check),
    )

    if not result.get("ok"):
        err_msg = result.get("error", "Gagal memproses video.")
        return f"{err_msg}", ""

    if result["ai_check_enabled"]:
        ai_summary = (
            f"**Status Deteksi AI:** {result['ai_status']}\n\n"
            f"_{result['ai_note']}_"
        )
    else:
        ai_summary = "**Status Deteksi AI:** Tidak diaktifkan (mode fokus ekstraksi informasi)."

    info_output = result["analysis"]
    if result.get("fallback_used"):
        info_output += "\n\n---\n_Catatan: Sistem otomatis menggunakan model/mode cadangan karena batas kuota atau rate limit model utama._"

    return ai_summary, info_output


with gr.Blocks(title="Analisis Video Media Sosial") as demo:
    gr.Markdown(
        "# Analisis Informasi & Indikasi Konten AI pada Video Media Sosial\n"
        f"Unggah file video pendek (disarankan **.mp4**, maks. **{MAX_VIDEO_SIZE_MB} MB**) "
        "atau coba masukkan tautan postingan (opsional)."
    )

    with gr.Row():
        with gr.Column(scale=1):
            video_input = gr.File(
                label="Upload Video (.mp4 — Utama)",
                file_types=[".mp4", ".mov", ".webm", ".mkv"],
                type="filepath",
            )
            url_input = gr.Textbox(
                label="Link Postingan Media Sosial (Opsional)",
                placeholder="https://...",
            )
            ai_checkbox = gr.Checkbox(
                label="Cek apakah konten berindikasi AI (Opsional)",
                value=False,
            )
            submit_btn = gr.Button("Analisis Video", variant="primary")

        with gr.Column(scale=1):
            ai_output = gr.Markdown(label="Indikasi Konten AI")
            analysis_output = gr.Markdown(label="Informasi dari Video")

    submit_btn.click(
        fn=handle_analyze,
        inputs=[video_input, url_input, ai_checkbox],
        outputs=[ai_output, analysis_output],
    )

if __name__ == "__main__":
    demo.launch()
