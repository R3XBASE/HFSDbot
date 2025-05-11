const { Telegraf } = require('telegraf');
const express = require('express');
const axios = require('axios');
const fs = require('fs');
const { promisify } = require('util');
const writeFile = promisify(fs.writeFile);
const unlink = promisify(fs.unlink);

const bot = new Telegraf(process.env.TELEGRAM_TOKEN);
const HF_API_KEY = process.env.HF_API_KEY;
const HF_API_URL = 'https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0';

// Inisialisasi Express untuk health check
const app = express();
const port = process.env.PORT || 3000;

// Konfigurasi logging
console.log = (...args) => {
  const timestamp = new Date().toISOString();
  process.stdout.write(`[${timestamp}] ${args.join(' ')}\n`);
};

// Health check endpoint untuk Render
app.get('/', (req, res) => {
  res.send('Bot is running');
});

// Handle perintah /start
bot.start((ctx) => ctx.reply('Halo! Saya bot pembuat gambar gratis. Kirim deskripsi gambar, misalnya: "A cat in a spaceship". Catatan: Generasi gambar bisa memakan waktu.'));

// Handle pesan teks
bot.on('text', async (ctx) => {
  const prompt = ctx.message.text;
  await ctx.reply(`Memproses: ${prompt}... Harap tunggu (bisa 10-30 detik).`);

  try {
    const response = await axios.post(
      HF_API_URL,
      {
        inputs: prompt,
        parameters: {
          num_inference_steps: 30,
          guidance_scale: 7.5,
        },
      },
      {
        headers: {
          Authorization: `Bearer ${HF_API_KEY}`,
          'Content-Type': 'application/json',
        },
        responseType: 'arraybuffer',
      }
    );

    if (response.status === 200) {
      const imagePath = `temp_image_${ctx.from.id}.png`;
      await writeFile(imagePath, response.data);
      await ctx.replyWithPhoto({ source: fs.createReadStream(imagePath) }, { caption: `Gambar untuk: ${prompt}` });
      await unlink(imagePath);
    } else {
      await ctx.reply(`Gagal menghasilkan gambar: ${response.statusText}`);
    }
  } catch (error) {
    console.error(error.message);
    await ctx.reply('Terjadi kesalahan saat menghasilkan gambar. Coba lagi nanti.');
  }
});

// Jalankan bot dan Express
bot.launch().then(() => {
  console.log('Bot sedang berjalan...');
  app.listen(port, () => {
    console.log(`Server berjalan di port ${port}`);
  });
}).catch((err) => {
  console.error('Gagal menjalankan bot:', err.message);
});

// Handle graceful shutdown
process.once('SIGINT', () => {
  bot.stop('SIGINT');
  process.exit(0);
});
process.once('SIGTERM', () => {
  bot.stop('SIGTERM');
  process.exit(0);
});
