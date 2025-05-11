import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, Filters, ContextTypes
import requests
import io
from PIL import Image
import os

# Konfigurasi logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Ganti dengan token bot Anda dari BotFather
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')  # Gunakan environment variable untuk keamanan

# Ganti dengan API key Hugging Face Anda
HF_API_KEY = os.getenv('HF_API_KEY')
HF_API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk perintah /start"""
    await update.message.reply_text(
        "Halo! Saya bot pembuat gambar gratis. Kirimkan deskripsi gambar, "
        "misalnya: 'A cat in a spaceship'. Catatan: Generasi gambar bisa memakan waktu."
    )

async def generate_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk menghasilkan dan mengirim gambar berdasarkan prompt"""
    prompt = update.message.text
    user = update.message.from_user

    await update.message.reply_text(f"Memproses: {prompt}... Harap tunggu (bisa 10-30 detik).")

    try:
        # Panggil Hugging Face API untuk menghasilkan gambar
        headers = {
            "Authorization": f"Bearer {HF_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "inputs": prompt,
            "parameters": {
                "num_inference_steps": 30,
                "guidance_scale": 7.5
            }
        }

        response = requests.post(HF_API_URL, headers=headers, json=payload)

        if response.status_code == 200:
            # Hugging Face mengembalikan gambar dalam format biner
            image_data = response.content
            image = Image.open(io.BytesIO(image_data))

            # Simpan gambar sementara
            image_path = f"temp_image_{user.id}.png"
            image.save(image_path)

            # Kirim gambar ke pengguna
            with open(image_path, 'rb') as photo:
                await update.message.reply_photo(photo=photo, caption=f"Gambar untuk: {prompt}")

            # Hapus file sementara
            os.remove(image_path)
        else:
            await update.message.reply_text(f"Gagal menghasilkan gambar: {response.text}")
    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text("Terjadi kesalahan saat menghasilkan gambar. Coba lagi nanti.")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk menangani error"""
    logger.error(f"Update {update} caused error {context.error}")
    if update is not None and update.message is not None:
        await update.message.reply_text("Terjadi kesalahan. Silakan coba lagi.")

def main():
    """Jalankan bot"""
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Tambahkan handler
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(Filters.text & ~Filters.command, generate_image))
    application.add_error_handler(error_handler)

    # Jalankan bot dengan polling
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
