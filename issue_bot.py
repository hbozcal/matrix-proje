import asyncio
from datetime import datetime
from nio import AsyncClient, MatrixRoom, Event, InviteEvent
from nio.responses import RoomContextResponse

# Kendi yazdığımız modüller
import config
import database
import gitlab_handler
from ai_handler import analyze_with_claude
from webhook_handler import send_to_nodejs_webhook_async, send_ai_analysis_to_nodejs_async
from media_handler import download_matrix_media_bruteforce
from voice_handler import transcribe_voice  

PROCESSING_EVENTS = set()
CLAUDE_ANALYSIS_CACHE = {}

async def invite_callback(room: MatrixRoom, event: InviteEvent):
    print(f"[*] {room.room_id} odasından davet alındı. Katılınıyor...")
    await client.join(room.room_id)

async def global_event_callback(room: MatrixRoom, event: Event):
    event_timestamp = event.source.get("origin_server_ts", 0)
    if event_timestamp < config.BOT_START_TIME:
        return
    
    event_dict = event.source
    event_type = event_dict.get("type")
    room_name = room.display_name or room.name

    if room_name not in config.ALLOWED_ROOM_NAMES:
        return

    # --- 1. MESAJ VE GÖRSEL YAKALAMA ---
    if event_type == "m.room.message":
        content = event_dict.get("content", {})
        msgtype = content.get("msgtype")
        sender = event_dict.get("sender", "")
        event_id = event_dict.get("event_id", "") 
        
        if "gitlab-bot" not in sender:
            msg_body = content.get("body", "İçerik Yok")
            await send_to_nodejs_webhook_async(event_id, room.room_id, sender, msg_body)

        if msgtype == "m.image" and "gitlab-bot" not in sender:
            print(f"\n[📸 DETEKTÖR] {room_name} odasında görsel algılandı! AI Analizi başlatılıyor...")
            mxc_url = content.get("url", "")
            
            if mxc_url and mxc_url.startswith("mxc://"):
                parts = mxc_url.split("/")
                image_bytes = await download_matrix_media_bruteforce(client.access_token, parts[2], parts[3])
                
                if image_bytes:
                    mime_type = content.get("info", {}).get("mime_type", "image/jpeg")
                    result = await analyze_with_claude(image_bytes, mime_type)
                    
                    if result:
                        await send_ai_analysis_to_nodejs_async(event_id, room.room_id, sender, result, mxc_url)
                        formatted_msg = (
                            f"📌 **Gelen Kargo / Belge Analizi**\n\n"
                            f"🏢 **Gönderen:** {result.get('gonderen', 'Okunamadı')}\n"
                            f"👤 **Alıcı:** {result.get('alici', 'Okunamadı')}\n"
                            f"📦 **İçerik:** {result.get('icerik', 'Okunamadı')}\n"
                            f"-----------\n"
                            f"🎫 **GitLab üzerinde kayıt oluşturulsun mu?** *(✅ emojisi bırakın)*"
                        )
                        resp = await client.room_send(room.room_id, message_type="m.room.message", content={"msgtype": "m.text", "body": formatted_msg})
                        if hasattr(resp, "event_id"):
                            CLAUDE_ANALYSIS_CACHE[resp.event_id] = {"ai_data": result, "room_name": room_name}

        if msgtype in ["m.audio", "m.voice"] and "gitlab-bot" not in sender:
            print(f"\n[🎤 SES DETEKTÖRÜ] {room_name} odasında ses algılandı! Deşifre ediliyor...")
            mxc_url = content.get("url", "")
            
            if mxc_url and mxc_url.startswith("mxc://"):
                parts = mxc_url.split("/")
                audio_bytes = await download_matrix_media_bruteforce(client.access_token, parts[2], parts[3])
                
                if audio_bytes:
                    transcript = await transcribe_voice(audio_bytes)
                    
                    if transcript:
                        print(f"[✅ DEŞİFRE BAŞARILI] Metin: {transcript}")
                        await send_to_nodejs_webhook_async(event_id, room.room_id, sender, transcript)
                        
                        await client.room_send(
                            room.room_id, 
                            message_type="m.room.message", 
                            content={
                                "msgtype": "m.text", 
                                "body": f"🎙️ **Sesli Mesaj Çevirisi:**\n{transcript}"
                            }
                        )

    # --- 2. REAKSİYON (EMOJİ) YAKALAMA ---
    elif event_type == "m.reaction":
        relation = event_dict.get("content", {}).get("m.relates_to", {})
        reaction_key = relation.get("key")
        target_event_id = relation.get("event_id")
        
        if not reaction_key or not target_event_id:
            return

        # ✅ AI KARGO ONAYI
        if "✅" in reaction_key and target_event_id in CLAUDE_ANALYSIS_CACHE:
            lock_key = f"claude_{target_event_id}"
            if lock_key in PROCESSING_EVENTS: return
            PROCESSING_EVENTS.add(lock_key)
            
            try:
                cache_item = CLAUDE_ANALYSIS_CACHE[target_event_id]
                ai_data = cache_item["ai_data"]
                timestamp_full = datetime.now(config.TZ_TURKEY).strftime("%d.%m.%Y %H:%M:%S")
                
                issue_title = f"Gelen Kargo: {ai_data.get('gonderen')} -> {ai_data.get('alici')}"
                issue_desc = f"## 📦 AI Kargo Kaydı\n* **Gönderen:** {ai_data.get('gonderen')}\n* **Alıcı:** {ai_data.get('alici')}\n* **İçerik:** {ai_data.get('icerik')}"
                
                gl_resp = await gitlab_handler.create_issue(issue_title, issue_desc, "WhatsApp, Kargo")
                if gl_resp.status_code == 201:
                    iid = gl_resp.json()['iid']
                    await database.save_processed_event(target_event_id, iid, room.room_id, timestamp_full)
                    
                    detailed_msg = (
                        f"Talebiniz için iş kaydı oluşturulmuştur.\n"
                        f"İş Kaydı No: #{iid}\n"
                        f"Başlık: Gelen Kargo - {ai_data.get('gonderen')} -> {ai_data.get('alici')}\n"
                        f"Oluşturulma Tarihi: {timestamp_full}"
                    )
                    await client.room_send(room.room_id, message_type="m.room.message", content={"msgtype": "m.text", "body": detailed_msg})
            finally:
                PROCESSING_EVENTS.discard(lock_key)

        # 📌 NORMAL İŞ KAYDI AÇMA
        elif "📌" in reaction_key:
            lock_key = f"pin_{target_event_id}"
            if lock_key in PROCESSING_EVENTS: return
            PROCESSING_EVENTS.add(lock_key)
            
            try:
                if await database.get_issue_by_event(target_event_id): return
                
                res = await client.room_context(room.room_id, target_event_id, limit=1)
                if res and res.event:
                    msg_body = getattr(res.event, "body", res.event.source.get("content", {}).get("body", "İçerik okunamadı."))
                    
                    gl_resp = await gitlab_handler.create_issue(f"WhatsApp Kaydı - {msg_body[:20]}...", f"**Mesaj:** {msg_body}", "WhatsApp, Üretim")
                    if gl_resp.status_code == 201:
                        iid = gl_resp.json()['iid']
                        timestamp_full = datetime.now(config.TZ_TURKEY).strftime("%d.%m.%Y %H:%M:%S")
                        await database.save_processed_event(target_event_id, iid, room.room_id, timestamp_full)
                        
                        detailed_msg = (
                            f"Talebiniz için iş kaydı oluşturulmuştur.\n"
                            f"İş Kaydı No: #{iid}\n"
                            f"Başlık: WhatsApp Kaydı - {msg_body[:20]}...\n"
                            f"Oluşturulma Tarihi: {timestamp_full}"
                        )
                        await client.room_send(room.room_id, message_type="m.room.message", content={"msgtype": "m.text", "body": detailed_msg})
            finally:
                PROCESSING_EVENTS.discard(lock_key)

        # 📝 YORUM EKLEME
        elif any(x in reaction_key for x in ["📝", "📄", "➕"]):
            lock_key = f"comment_{target_event_id}"
            if lock_key in PROCESSING_EVENTS: return
            PROCESSING_EVENTS.add(lock_key)
            
            try:
                iid = await database.get_latest_issue_by_room(room.room_id)
                if not iid: return
                
                res = await client.room_context(room.room_id, target_event_id, limit=1)
                if res and res.event:
                    msg_body = getattr(res.event, "body", "")
                    gl_resp = await gitlab_handler.add_comment(iid, f"💬 **Ek Bilgi:**\n\n> {msg_body}")
                    if gl_resp.status_code == 201:
                        await client.room_send(room.room_id, message_type="m.room.message", content={"msgtype": "m.text", "body": f"📝 #{iid} nolu kayda yorum eklendi."})
            finally:
                PROCESSING_EVENTS.discard(lock_key)

        # 👇 GÜNCELLENEN İŞ KAYDI KAPATMA BLOĞU 👇
        elif any(x in reaction_key for x in ["❌", "✖️", "✖"]):
            try:
                iid = await database.get_issue_by_event(target_event_id) or await database.get_latest_issue_by_room(room.room_id)
                if iid:
                    if (await gitlab_handler.close_issue(iid)).status_code == 200:
                        timestamp_full = datetime.now(config.TZ_TURKEY).strftime("%d.%m.%Y %H:%M:%S")
                        
                        detailed_close_msg = (
                            f"🔒 İş kaydı kapatılmıştır.\n"
                            f"İş Kaydı No: #{iid}\n"
                            f"Kapatılma Tarihi: {timestamp_full}"
                        )
                        await client.room_send(room.room_id, message_type="m.room.message", content={"msgtype": "m.text", "body": detailed_close_msg})
            except Exception: pass
        # 👆 BİTİŞ 👆

async def main():
    global client
    await database.init_db()
    
    print("Matrix sunucusuna bağlanılıyor...")
    client = AsyncClient(config.HOMESERVER, config.BOT_USER)
    client.access_token = config.BOT_TOKEN
    
    client.add_event_callback(invite_callback, InviteEvent)
    client.add_event_callback(global_event_callback, Event)

    print("Bağlantı başarılı! Modüler Bot Aktif...")
    await client.sync_forever(timeout=30000)

if __name__ == "__main__":
    asyncio.run(main())