from flask import Flask, request
import requests

app = Flask(__name__)

# Matrix Ayarlarımız
MATRIX_URL = "http://localhost:8008"
ROOM_ID = "!ILghHqsFAZrhyGImub:localhost"
ACCESS_TOKEN = "syt_Z2l0bGFiLWJvdA_nmPnxFaOotBZMABBZpZc_3QxPVx"

def send_to_matrix(plain_text, html_text):
    """Matrix odasına mesaj fırlatan fonksiyon"""
    url = f"{MATRIX_URL}/_matrix/client/r0/rooms/{ROOM_ID}/send/m.room.message?access_token={ACCESS_TOKEN}"
    
    payload = {
        "msgtype": "m.text",
        "body": plain_text,
        "format": "org.matrix.custom.html",
        "formatted_body": html_text
    }
    
    requests.post(url, json=payload)

@app.route('/webhook', methods=['POST'])
def gitlab_webhook():
    """GitLab'dan gelen bildirimleri yakalayan kapı"""
    data = request.json
    event_type = request.headers.get('X-Gitlab-Event', '')
    
    # Eğer gelen bildirim bir kod yükleme (Push) işlemiyse:
    if event_type == "Push Hook":
        # BURAYI GÜNCELLEDİK: Eğer GitLab'dan bir isim gelmezse varsayılan olarak Harun Bozçal yazacak
        user_name = data.get('user_name', 'Harun Bozçal')
        project_name = data.get('project', {}).get('name', 'Matrix Projesi')
        commits = data.get('commits', [])
        
        # Gönderilen kod (commit) mesajlarını listele
        commit_messages = "<br>".join([f"• {c['message'].strip()}" for c in commits])
        
        # Matrix'te görünecek şık HTML mesajını hazırla
        html_msg = f"🚀 <b>{user_name}</b>, <i>{project_name}</i> projesine {len(commits)} yeni kod (commit) gönderdi:<br><br>{commit_messages}"
        plain_msg = f"{user_name}, {project_name} projesine yeni kodlar gönderdi."
        
        # Matrix'e yolla!
        send_to_matrix(plain_msg, html_msg)
        
    return "Başarılı", 200

if __name__ == '__main__':
    # Botu 5000 portunda çalıştır
    print("🤖 GitLab-Matrix köprüsü çalışıyor... Bekleniyor.")
    app.run(host='0.0.0.0', port=5000)

   
   #veritabanına gönderme 
    import requests
from datetime import datetime

def send_to_nodejs_webhook(event_id, room_id, sender_id, sender_name, message_text):
    """
    Matrix'ten gelen mesajı Node.js (Express) sunucumuza postalar.
    """
    webhook_url = "http://localhost:3000/api/v1/messages"
    
    # Node.js tarafında beklediğimiz (normalize edilmiş) JSON formatı
    payload = {
        "messageId": event_id,
        "eventId": event_id,
        "roomId": room_id,
        "platform": "matrix", # Veya WhatsApp'tan geliyorsa 'whatsapp' yapılabilir
        "sender": { 
            "id": sender_id, 
            "name": sender_name 
        },
        "type": "text",
        "content": { "text": message_text },
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

    try:
        # Mesajı Node.js sunucusuna fırlatıyoruz
        response = requests.post(webhook_url, json=payload, timeout=5)
        
        # 202 Accepted bekliyoruz (Controller'da öyle ayarlamıştık)
        if response.status_code == 202:
            print(f"[Webhook] Mesaj Node.js'e başarıyla iletildi: {event_id}")
        else:
            print(f"[Webhook Hata] Node.js reddetti: {response.status_code} - {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"[Webhook Kritik Hata] Node.js sunucusuna ulaşılamadı: {e}")