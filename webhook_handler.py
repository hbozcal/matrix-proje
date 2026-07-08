import asyncio
import requests
from datetime import datetime, timezone
import config

async def send_to_nodejs_webhook_async(event_id, room_id, sender_id, message_text):
    payload = {
        "messageId": event_id,
        "eventId": event_id,
        "roomId": room_id,
        "platform": "whatsapp" if "whatsapp" in sender_id.lower() else "matrix",
        "sender": { "id": sender_id, "name": sender_id },
        "type": "text",
        "content": { "text": message_text },
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    }

    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: requests.post(config.WEBHOOK_URL, json=payload, timeout=5))
    except Exception as e:
        print(f"[Webhook Kritik Hata] Node.js sunucusuna ulaşılamadı: {e}")

async def send_ai_analysis_to_nodejs_async(event_id, room_id, sender_id, ai_data, mxc_url):
    payload = {
        "messageId": f"ai_{event_id}", 
        "eventId": event_id,
        "roomId": room_id,
        "platform": "whatsapp" if "whatsapp" in sender_id.lower() else "matrix",
        "sender": { "id": "claude-ai", "name": "Claude AI" },
        "type": "image_analysis",
        "content": { 
            "text": "Kargo/İrsaliye Görsel Analizi",
            "imageUrl": mxc_url, 
            "aiResult": ai_data  
        },
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    }

    try:
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, lambda: requests.post(config.WEBHOOK_URL, json=payload, timeout=5))
        if response.status_code == 202:
            print(f"[Webhook] 🧠 AI Analizi Node.js'e başarıyla iletildi: ai_{event_id}")
    except Exception as e:
        print(f"[Webhook Kritik Hata] AI verisi gönderilirken sunucuya ulaşılamadı: {e}")