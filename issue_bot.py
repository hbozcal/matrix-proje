import asyncio
import requests
import base64
import json
from datetime import datetime, timezone, timedelta
from nio import AsyncClient, MatrixRoom, Event, InviteEvent
from nio.responses import RoomContextResponse
from anthropic import Anthropic

import database

# --- KONFİGÜRASYON ---
HOMESERVER = "http://localhost:8008"
BOT_USER = "@gitlab-bot:localhost"
BOT_TOKEN = "syt_Z2l0bGFiLWJvdA_nmPnxFaOotBZMABBZpZc_3QxPVx"

# GitLab Ayarları
GITLAB_URL = "https://gitlab.com" 
GITLAB_PROJECT_ID = "83126217" 
GITLAB_TOKEN = "glpat-c0vhEv5sjRisdnqGIK1Qj2M6MQpvOjEKdTpuOHN1bA8.01.1719eb39r" 

# Claude AI Ayarı
ANTHROPIC_API_KEY = "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"

ALLOWED_ROOM_NAMES = ["Üretim", "üretim", "Yazılım", "yazılım", "YAZILIM", "Uretim_Test"]

# Türkiye Saat Dilimi Sabiti
TZ_TURKEY = timezone(timedelta(hours=3))

# --- ASENKRON YARIŞ DURUMU (RACE CONDITION) ÖNLEYİCİ ---
PROCESSING_EVENTS = set()

# --- CLAUDE GEÇİCİ BELLEK CACHE ---
CLAUDE_ANALYSIS_CACHE = {}

# Claude İstemcisini Başlat
claude_client = Anthropic(api_key=ANTHROPIC_API_KEY)


async def analyze_with_claude(image_bytes, mime_type):
    """Görseli bloke etmeden arka planda Claude AI'a gönderir ve yanıtı filtreler"""
    base64_image = base64.b64encode(image_bytes).decode("utf-8")
    
    prompt = """Sen bir kargo, fatura ve irsaliye analiz uzmanısın.
Görseldeki belgeyi, etiketi veya paketi incele. 
Yanıtını KESİNLİKLE başka hiçbir açıklama metni eklemeden, doğrudan şu JSON formatında döndür:
{
  "gonderen": "Kim göndermiş (Firma veya Kişi adı, okunamıyorsa 'Tespit Edilemedi' yaz)",
  "alici": "Kime göndermiş (Firma veya Kişi adı, okunamıyorsa 'Tespit Edilemedi' yaz)",
  "icerik": "Ne gelmiş (Etikette yazan ürün, paket veya evrak detayı, okunamıyorsa 'Bilinmiyor' yaz)"
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
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": mime_type,
                                "data": base64_image,
                            },
                        },
                        {
                            "type": "text",
                            "text": "Bu görseli analiz et ve belirtilen JSON formatında yanıt ver."
                        }
                    ],
                }
            ],
        ))
        
        # Claude'un döndürdüğü ham metni alıyoruz
        raw_text = response.content[0].text
        print(f"\n[DEBUG] Claude'dan Gelen Ham Yanıt:\n{raw_text}\n")
        
        # Gevezelik filtresi: Sadece süslü parantezlerin { } arasındaki JSON'ı cımbızla
        start_idx = raw_text.find('{')
        end_idx = raw_text.rfind('}') + 1
        
        if start_idx != -1 and end_idx != 0:
            json_str = raw_text[start_idx:end_idx]
            return json.loads(json_str)
        else:
            raise ValueError("Gelen yanıtta geçerli bir JSON formatı bulunamadı.")
            
    except Exception as e:
        print(f"[-] Claude API Analiz Hatası: {e}")
        return None
    """Görseli bloke etmeden arka planda Claude Sonnet 4.6'ya gönderir"""
    base64_image = base64.b64encode(image_bytes).decode("utf-8")
    
    prompt = """Sen bir kargo, fatura ve irsaliye analiz uzmanısın.
Görseldeki belgeyi, etiketi veya paketi incele. 
Yanıtını KESİNLİKLE başka hiçbir açıklama metni eklemeden, doğrudan şu JSON formatında döndür:
{
  "gonderen": "Kim göndermiş (Firma veya Kişi adı, okunamıyorsa 'Tespit Edilemedi' yaz)",
  "alici": "Kime göndermiş (Firma veya Kişi adı, okunamıyorsa 'Tespit Edilemedi' yaz)",
  "icerik": "Ne gelmiş (Etikette yazan ürün, paket veya evrak detayı, okunamıyorsa 'Bilinmiyor' yaz)"
}"""

    try:
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, lambda: claude_client.messages.create(
            # YENİ EKLENEN KISIM: Hesap tier uyumluluğu için stabil Haziran sürümü kullanılıyor
            model="claude-sonnet-4-6",
            max_tokens=500,
            temperature=0.0,
            system=prompt,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": mime_type,
                                "data": base64_image,
                            },
                        },
                        {
                            "type": "text",
                            "text": "Bu görseli analiz et ve belirtilen JSON formatında yanıt ver."
                        }
                    ],
                }
            ],
        ))
        return json.loads(response.content[0].text)
    except Exception as e:
        print(f"[-] Claude API Analiz Hatası: {e}")
        return None


async def download_matrix_media_bruteforce(access_token, mxc_server, media_id):
    """Matrix sunucusundan medyayı Token (Kimlik) ile güvenli ve zorla indirir."""
    loop = asyncio.get_event_loop()
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # 1. Yöntem: Matrix v1.11+ Güncel Authenticated (Kimlik Doğrulamalı) Endpoint
    url_new = f"{HOMESERVER}/_matrix/client/v1/media/download/{mxc_server}/{media_id}"
    # 2. Yöntem: Eski Legacy Endpoint
    url_legacy = f"{HOMESERVER}/_matrix/media/v3/download/{mxc_server}/{media_id}"
    
    def fetch_url(url):
        try:
            r = requests.get(url, headers=headers, timeout=15)
            if r.status_code == 200:
                return r.content
            return r.status_code
        except Exception as e:
            return str(e)

    # Önce yeni API'yi deniyoruz
    res_new = await loop.run_in_executor(None, fetch_url, url_new)
    if isinstance(res_new, bytes):
        return res_new
        
    print(f"[LOG] Yeni nesil Matrix Medya API yanıt vermedi (Durum: {res_new}). Legacy yola düşülüyor...")
    
    # Yeni API patlarsa eski API'yi deniyoruz
    res_legacy = await loop.run_in_executor(None, fetch_url, url_legacy)
    if isinstance(res_legacy, bytes):
        return res_legacy
        
    print(f"[-] Kritik Hata: Her iki indirme yöntemi de başarısız oldu! Legacy Sunucu Yanıtı: {res_legacy}")
    return None


async def invite_callback(room: MatrixRoom, event: InviteEvent):
    """Davetleri otomatik kabul eder."""
    print(f"[*] {room.room_id} odasından davet alındı. Katılınıyor...")
    try:
        await client.join(room.room_id)
    except Exception as e:
        print(f"[-] Odaya katılamadı: {e}")


async def global_event_callback(room: MatrixRoom, event: Event):
    """Tüm eventleri dinler, filtreleri uygular ve analiz süreçlerini yönetir."""
    event_dict = event.source
    event_type = event_dict.get("type")
    room_name = room.display_name or room.name

    if room_name not in ALLOWED_ROOM_NAMES:
        return

    # -----------------------------------------------------------------
    # 📸 GÖRSEL TESPİTİ VE İNDİRME
    # -----------------------------------------------------------------
    if event_type == "m.room.message":
        content = event_dict.get("content", {})
        msgtype = content.get("msgtype")
        sender = event_dict.get("sender", "")
        
        if msgtype == "m.image" and "gitlab-bot" not in sender:
            print(f"\n[📸 DETEKTÖR] {room_name} odasında görsel algılandı! AI Analizi başlatılıyor...")
            mxc_url = content.get("url", "")
            
            if mxc_url and mxc_url.startswith("mxc://"):
                try:
                    parts = mxc_url.split("/")
                    mxc_server = parts[2]
                    media_id = parts[3]
                    
                    print(f"[LOG] Balyoz İndirme Metodu devrede: Sunucu={mxc_server}, Medya={media_id}")
                    
                    image_bytes = await download_matrix_media_bruteforce(client.access_token, mxc_server, media_id)
                    
                    if image_bytes:
                        print("[🧠 AI] Görsel başarıyla indirildi! Claude 3.5 Sonnet Kargo/İrsaliye analizini yapıyor...")
                        mime_type = content.get("info", {}).get("mime_type", "image/jpeg")
                        
                        result = await analyze_with_claude(image_bytes, mime_type)
                        
                        if result:
                            print("[🎉 BAŞARILI] AI Yanıt verdi, odaya mesaj gönderiliyor...")
                            formatted_msg = (
                                f"📌 **Gelen Kargo / Belge Analizi**\n\n"
                                f"🏢 **Kim Göndermiş:** {result.get('gonderen', 'Okunamadı')}\n"
                                f"👤 **Kime Göndermiş:** {result.get('alici', 'Okunamadı')}\n"
                                f"📦 **Ne Gelmiş:** {result.get('icerik', 'Okunamadı')}\n"
                                f"-----------\n"
                                f"🎫 **GitLab üzerinde kayıt oluşturulsun mu?**\n"
                                f"*(Onaylamak için bu mesaja ✅ emojisi bırakın)*"
                            )
                            
                            resp = await client.room_send(
                                room.room_id, 
                                message_type="m.room.message", 
                                content={"msgtype": "m.text", "body": formatted_msg}
                            )
                            
                            if hasattr(resp, "event_id"):
                                CLAUDE_ANALYSIS_CACHE[resp.event_id] = {
                                    "ai_data": result,
                                    "room_name": room_name
                                }
                                print(f"[📨] Kargo analiz raporu odaya gönderildi, ✅ onayı bekleniyor.")
                        else:
                            print("[-] AI analizi başarısız oldu (API yanıt veremedi).")
                    else:
                        print(f"[-] Synapse sunucusu medya indirmeyi kesin olarak reddetti.")
                except Exception as ex:
                    print(f"[-] Görsel URL ayrıştırma veya indirme hatası: {ex}")

    # -----------------------------------------------------------------
    # REAKSİYON (EMOJİ) YAKALAYICI
    # -----------------------------------------------------------------
    elif event_type == "m.reaction":
        relation = event_dict.get("content", {}).get("m.relates_to", {})
        reaction_key = relation.get("key")
        target_event_id = relation.get("event_id")
        
        if not reaction_key or not target_event_id:
            return

        try:
            res = await client.room_context(room.room_id, target_event_id, limit=1)
            if res and isinstance(res, RoomContextResponse) and res.event:
                msg_sender = getattr(res.event, "sender", "")
                if "✅" not in reaction_key and ("gitlab-bot" in msg_sender or "whatsappbot" in msg_sender):
                    return
        except Exception:
            pass

        # -----------------------------------------------------------------
        # ✅ REAKSİYONU - AI KARGO ONAYI
        # -----------------------------------------------------------------
        if "✅" in reaction_key:
            if target_event_id in CLAUDE_ANALYSIS_CACHE:
                lock_key = f"claude_{target_event_id}"
                if lock_key in PROCESSING_EVENTS:
                    return
                PROCESSING_EVENTS.add(lock_key)
                
                try:
                    print(f"\n[🚀 ONAY] Kargo kaydı onaylandı! GitLab Issue açılıyor...")
                    cache_item = CLAUDE_ANALYSIS_CACHE[target_event_id]
                    ai_data = cache_item["ai_data"]
                    r_name = cache_item["room_name"]
                    
                    now_tr = datetime.now(TZ_TURKEY)
                    timestamp_full = now_tr.strftime("%Y-%m-%d %H:%M:%S")
                    
                    gl_url = f"{GITLAB_URL}/api/v4/projects/{GITLAB_PROJECT_ID}/issues"
                    gl_headers = {"PRIVATE-TOKEN": GITLAB_TOKEN}
                    
                    issue_title = f"Gelen Kargo: {ai_data.get('gonderen', 'Bilinmeyen')} -> {ai_data.get('alici', 'Bilinmeyen')}"
                    
                    issue_description = (
                        f"## 📦 Gelen Evrak / Kargo Kaydı (AI Destekli)\n\n"
                        f"* **Kim Göndermiş:** {ai_data.get('gonderen', 'Belirtilmedi')}\n"
                        f"* **Kime Göndermiş:** {ai_data.get('alici', 'Belirtilmedi')}\n"
                        f"* **Ne Gelmiş:** {ai_data.get('icerik', 'Belirtilmedi')}\n\n"
                        f"---\n"
                        f"*📍 Kaynak Oda: `{r_name}`*\n"
                        f"*📅 Kayıt Zamanı: `{timestamp_full}`*\n"
                        f"*Bu kayıt WhatsApp üzerinden gelen görselin Claude AI tarafından analiz edilmesiyle otomatik oluşturulmuştur.*"
                    )
                    
                    gl_payload = {"title": issue_title, "description": issue_description, "labels": "WhatsApp, Kargo"}
                    loop = asyncio.get_event_loop()
                    gl_response = await loop.run_in_executor(None, lambda: requests.post(gl_url, headers=gl_headers, json=gl_payload, timeout=10))
                    
                    if gl_response.status_code == 201:
                        issue_data = gl_response.json()
                        current_iid = issue_data['iid']
                        
                        await database.save_processed_event(target_event_id, current_iid, room.room_id, timestamp_full)
                        
                        success_msg = (
                            f"✅ **Kargo Kaydı Başarıyla Oluşturuldu!**\n"
                            f"🔹 **İş Kaydı No:** #{current_iid}\n"
                            f"🔹 **Başlık:** {issue_title}\n"
                            f"🔗 **Link:** {issue_data.get('web_url')}"
                        )
                        await client.room_send(room.room_id, message_type="m.room.message", content={"msgtype": "m.text", "body": success_msg})
                        del CLAUDE_ANALYSIS_CACHE[target_event_id]
                except Exception as e:
                    print(f"[-] Claude Issue oluşturulurken hata: {e}")
                finally:
                    PROCESSING_EVENTS.discard(lock_key)
                return

        # -----------------------------------------------------------------
        # 📌 PIN REAKSİYONU - NORMAL YAZI TALEBİ AÇMA
        # -----------------------------------------------------------------
        elif "📌" in reaction_key:
            lock_key = f"pin_{target_event_id}"
            if lock_key in PROCESSING_EVENTS:
                return
            
            PROCESSING_EVENTS.add(lock_key)
            try:
                print(f"\n[🔬 DETEKTÖR] {room_name} odasında 📌 reaksiyonu yakalandı!")
                
                existing_issue_iid = await database.get_issue_by_event(target_event_id)
                if existing_issue_iid:
                    warning_msg = f"⚠️ Bu mesaj için zaten bir iş kaydı oluşturulmuştur!\nİş Kaydı No: #{existing_issue_iid}"
                    await client.room_send(room.room_id, message_type="m.room.message", content={"msgtype": "m.text", "body": warning_msg})
                    return

                await asyncio.sleep(0.5)
                res = await client.room_context(room.room_id, target_event_id, limit=1)
                if res and isinstance(res, RoomContextResponse) and res.event:
                    
                    if hasattr(res.event, "body"):
                        msg_body = res.event.body
                    else:
                        msg_body = res.event.source.get("content", {}).get("body", "İçerik gövdesi okunamadı.")
                        
                    sender = getattr(res.event, "sender", "Bilinmeyen Kullanıcı")
                    
                    now_tr = datetime.now(TZ_TURKEY)
                    created_at_date = now_tr.strftime("%d.%m.%Y")
                    created_at_time = now_tr.strftime("%H:%M:%S")
                    timestamp_full = now_tr.strftime("%Y-%m-%d %H:%M:%S")
                    
                    gl_url = f"{GITLAB_URL}/api/v4/projects/{GITLAB_PROJECT_ID}/issues"
                    gl_headers = {"PRIVATE-TOKEN": GITLAB_TOKEN}
                    issue_title = f"WhatsApp Kaydı - {msg_body[:30]}..."
                    issue_description = (
                        f"### 📱 Otomatik WhatsApp İş Kaydı\n\n"
                        f"**💬 Mesaj İçeriği:** {msg_body}\n\n"
                        f"---\n"
                        f"**👤 Gönderen Kullanıcı:** `{sender}`\n"
                        f"**📍 Kaynak Oda:** `{room_name}`\n\n"
                        f"### 📅 Zaman Bilgileri (Europe/Istanbul)\n"
                        f"* **Oluşturulma Tarihi:** {created_at_date}\n"
                        f"* **Oluşturulma Saati:** {created_at_time}\n"
                        f"* **Timestamp:** `{timestamp_full}`\n"
                    )
                    
                    gl_payload = {"title": issue_title, "description": issue_description, "labels": "WhatsApp, Üretim"}
                    loop = asyncio.get_event_loop()
                    gl_response = await loop.run_in_executor(None, lambda: requests.post(gl_url, headers=gl_headers, json=gl_payload, timeout=10))

                    if gl_response.status_code == 201:
                        issue_data = gl_response.json()
                        current_iid = issue_data['iid']
                        await database.save_processed_event(target_event_id, current_iid, room.room_id, timestamp_full)
                        
                        whatsapp_success_msg = (
                            f"Talebiniz için iş kaydı oluşturulmuştur.\n"
                            f"İş Kaydı No: #{current_iid}\n"
                            f"Başlık: {issue_title}\n"
                            f"Oluşturulma Tarihi: {created_at_date} {created_at_time}"
                        )
                        await client.room_send(room.room_id, message_type="m.room.message", content={"msgtype": "m.text", "body": whatsapp_success_msg})
            except Exception as e:
                print(f"[-] Issue oluşturulurken hata: {e}")
            finally:
                PROCESSING_EVENTS.discard(lock_key)

        # -----------------------------------------------------------------
        # 📝 REAKSİYONU - YORUM EKLEME
        # -----------------------------------------------------------------
        elif any(x in reaction_key for x in ["📝", "📄", "➕"]):
            lock_key = f"comment_{target_event_id}"
            if lock_key in PROCESSING_EVENTS:
                return
                
            PROCESSING_EVENTS.add(lock_key)
            try:
                target_issue_iid = await database.get_latest_issue_by_room(room.room_id)
                if not target_issue_iid:
                    return

                await asyncio.sleep(0.5)
                res = await client.room_context(room.room_id, target_event_id, limit=1)
                if res and isinstance(res, RoomContextResponse) and res.event:
                    
                    if hasattr(res.event, "body"):
                        comment_body = res.event.body
                    else:
                        comment_body = res.event.source.get("content", {}).get("body", "İçerik gövdesi okunamadı.")
                        
                    comment_sender = getattr(res.event, "sender", "Bilinmeyen Kullanıcı")
                    
                    now_tr = datetime.now(TZ_TURKEY)
                    time_str = now_tr.strftime("%d.%m.%Y %H:%M:%S")

                    gl_url = f"{GITLAB_URL}/api/v4/projects/{GITLAB_PROJECT_ID}/issues/{target_issue_iid}/notes"
                    gl_headers = {"PRIVATE-TOKEN": GITLAB_TOKEN}
                    gl_payload = {
                        "body": f"💬 **WhatsApp'tan Ek Bilgi/Yorum:**\n\n> {comment_body}\n\n* **Gönderen:** `{comment_sender}`\n* **Ekleme Tarihi:** {time_str}"
                    }
                    
                    loop = asyncio.get_event_loop()
                    gl_response = await loop.run_in_executor(None, lambda: requests.post(gl_url, headers=gl_headers, json=gl_payload, timeout=10))

                    if gl_response.status_code == 201:
                        success_comment_msg = f"📝 **Ek Bilgi Eklendi!**\nİlgili mesaj, #{target_issue_iid} nolu iş kaydına yorum olarak işlenmiştir."
                        await client.room_send(room.room_id, message_type="m.room.message", content={"msgtype": "m.text", "body": success_comment_msg})
            except Exception as e:
                print(f"[-] Yorum eklenirken hata: {e}")
            finally:
                PROCESSING_EVENTS.discard(lock_key)

        # -----------------------------------------------------------------
        # ❌ REAKSİYONU - ISSUE KAPATMA
        # -----------------------------------------------------------------
        elif any(x in reaction_key for x in ["❌", "✖️", "✖"]):
            lock_key = f"close_{target_event_id}"
            if lock_key in PROCESSING_EVENTS:
                return
                
            PROCESSING_EVENTS.add(lock_key)
            try:
                target_issue_iid = await database.get_issue_by_event(target_event_id)
                if not target_issue_iid:
                    target_issue_iid = await database.get_latest_issue_by_room(room.room_id)

                if not target_issue_iid:
                    return

                gl_url = f"{GITLAB_URL}/api/v4/projects/{GITLAB_PROJECT_ID}/issues/{target_issue_iid}"
                gl_headers = {"PRIVATE-TOKEN": GITLAB_TOKEN}
                gl_payload = {"state_event": "close"}
                
                loop = asyncio.get_event_loop()
                gl_response = await loop.run_in_executor(None, lambda: requests.put(gl_url, headers=gl_headers, json=gl_payload, timeout=10))

                if gl_response.status_code == 200:
                    close_msg = f"🔒 **İş Kaydı Kapatıldı!**\n#{target_issue_iid} nolu talep başarıyla çözümlenmiş ve kapatılmıştır."
                    await client.room_send(room.room_id, message_type="m.room.message", content={"msgtype": "m.text", "body": close_msg})
            except Exception as e:
                pass
            finally:
                PROCESSING_EVENTS.discard(lock_key)


async def main():
    global client
    await database.init_db()
    
    print("Matrix sunucusuna bağlanılıyor...")
    client = AsyncClient(HOMESERVER, BOT_USER)
    client.access_token = BOT_TOKEN
    
    client.add_event_callback(invite_callback, InviteEvent)
    client.add_event_callback(global_event_callback, Event)

    print("Bağlantı başarılı! Bot aktif, Gelişmiş Kimlik Doğrulamalı Medya Modu ve Sonnet 0620 devrede...")
    await client.sync_forever(timeout=30000)

if __name__ == "__main__":
    asyncio.run(main())