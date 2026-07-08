import asyncio
import base64
import json
import os
import hashlib
from anthropic import Anthropic
import config

claude_client = Anthropic(api_key=config.ANTHROPIC_API_KEY)

# --- TASARRUF SİSTEMİ AYARLARI ---
HASH_FILE = "processed_images.json"

def get_image_hash(image_bytes):
    """Görselin bayt verisinden eşsiz bir parmak izi (SHA-256) oluşturur."""
    return hashlib.sha256(image_bytes).hexdigest()

def is_image_processed(img_hash):
    """Görselin parmak izi daha önce kaydedilmiş mi diye bakar."""
    if not os.path.exists(HASH_FILE):
        return False
        
    with open(HASH_FILE, "r") as f:
        try:
            hashes = json.load(f)
            return img_hash in hashes
        except json.JSONDecodeError:
            return False

def mark_image_processed(img_hash):
    """Görselin parmak izini işlenmişler listesine kaydeder."""
    hashes = []
    if os.path.exists(HASH_FILE):
        with open(HASH_FILE, "r") as f:
            try:
                hashes = json.load(f)
            except json.JSONDecodeError:
                hashes = []
                
    if img_hash not in hashes:
        hashes.append(img_hash)
        with open(HASH_FILE, "w") as f:
            json.dump(hashes, f)

async def analyze_with_claude(image_bytes, mime_type):
    """Görseli Claude AI'a gönderir (Mükerrer kontrolü ile)."""
    
    # 1. MÜKERRER KONTROLÜ (Tasarruf Freni)
    img_hash = get_image_hash(image_bytes)
    
    if is_image_processed(img_hash):
        print(f"\n[♻️ TASARRUF AKTİF] Bu görsel daha önce analiz edilmiş! Claude'a tekrar gönderilmiyor (Token korundu).")
        return None

    base64_image = base64.b64encode(image_bytes).decode("utf-8")
    
    prompt = """Sen bir kargo, fatura ve irsaliye analiz uzmanısın.
Görseldeki belgeyi, etiketi veya paketi incele. 
Yanıtını KESİNLİKLE başka hiçbir açıklama metni eklemeden, doğrudan şu JSON formatında döndür:
{
  "gonderen": "...",
  "alici": "...",
  "icerik": "..."
}"""

    try:
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, lambda: claude_client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=500,
            temperature=0.0,
            system=prompt,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "image", "source": {"type": "base64", "media_type": mime_type, "data": base64_image}},
                        {"type": "text", "text": "Bu görseli analiz et ve belirtilen JSON formatında yanıt ver."}
                    ],
                }
            ],
        ))
        
        raw_text = response.content[0].text
        start_idx = raw_text.find('{')
        end_idx = raw_text.rfind('}') + 1
        
        if start_idx != -1 and end_idx != 0:
            # 2. BAŞARILI ANALİZ SONRASI PARMAK İZİNİ KAYDET
            mark_image_processed(img_hash)
            print(f"[🧠 AI] Analiz başarılı. Görselin parmak izi sisteme kaydedildi.")
            return json.loads(raw_text[start_idx:end_idx])
        else:
            raise ValueError("Gelen yanıtta JSON formatı bulunamadı.")
            
    except Exception as e:
        print(f"[-] Claude API Analiz Hatası: {e}")
        return None