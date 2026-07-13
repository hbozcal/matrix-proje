import asyncio
import os
import tempfile
import whisper

import config

# FFmpeg yolu artık hardcoded değil, .env üzerinden geliyor (opsiyonel).
# Sunucu Linux ise genelde FFmpeg zaten PATH içindedir; sadece Windows'ta
# özel bir kurulum yolu varsa FFMPEG_PATH tanımlanmalı.
if config.FFMPEG_PATH and config.FFMPEG_PATH not in os.environ["PATH"]:
    os.environ["PATH"] += os.path.pathsep + config.FFMPEG_PATH

print(f"[🤖 LOCAL WHISPER] '{config.WHISPER_MODEL}' modeli yükleniyor (Hafızaya alınıyor)...")
whisper_model = whisper.load_model(config.WHISPER_MODEL)
print("[✅ LOCAL WHISPER] Model başarıyla yüklendi ve kullanıma hazır!")


async def transcribe_voice(audio_bytes: bytes) -> str:
    """
    Gelen ses byte verisini yerel Whisper modeli ile metne çevirir.
    """
    temp_path = None
    try:
        # 1. Gelen ses byte verisini geçici bir dosyaya yazıyoruz
        with tempfile.NamedTemporaryFile(delete=False, suffix=".ogg") as temp_audio:
            temp_audio.write(audio_bytes)
            temp_path = temp_audio.name

        print(f"[🎤 LOCAL WHISPER] Ses deşifre ediliyor: {temp_path}")

        # 2. Whisper senkron çalıştığı için asyncio.to_thread kullanarak ana botu kilitlemesini önlüyoruz
        result = await asyncio.to_thread(
            whisper_model.transcribe,
            temp_path,
            language=config.WHISPER_LANGUAGE,
        )

        return result.get("text", "").strip()

    except Exception as e:
        print(f"[❌ LOCAL WHISPER HATASI] Transkripsiyon başarısız: {e}")
        return ""

    finally:
        # 3. İşlem bittikten/hata alındıktan sonra geçici dosyayı her durumda temizle
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
