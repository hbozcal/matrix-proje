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