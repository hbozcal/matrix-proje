import asyncio
import os
import tempfile
import whisper

# Windows arka plan servisleri için FFmpeg yolunu kod seviyesinde kesinleştiriyoruz
FFMPEG_PATH = r"C:\ffmpeg\bin"
if FFMPEG_PATH not in os.environ["PATH"]:
    os.environ["PATH"] += os.path.pathsep + FFMPEG_PATH

print("[🤖 LOCAL WHISPER] Model yükleniyor (Hafızaya alınıyor)...")
whisper_model = whisper.load_model("base")
print("[✅ LOCAL WHISPER] Model başarıyla yüklendi ve kullanıma hazır!")

async def transcribe_voice(audio_bytes: bytes) -> str:
    """
    Gelen ses byte verisini yerel Whisper modeli ile Türkçe metne çevirir.
    """
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
            language="tr"
        )
        
        # 3. İşlem bittikten sonra geçici dosyayı bilgisayardan temizliyoruz
        if os.path.exists(temp_path):
            os.remove(temp_path)
            
        return result.get("text", "").strip()

    except Exception as e:
        print(f"[❌ LOCAL WHISPER HATASI] Transkripsiyon başarısız: {e}")
        return ""