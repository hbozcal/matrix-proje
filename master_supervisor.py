import subprocess
import time
import threading
import sys

# --- ÇALIŞTIRILACAK VE DENETLENECEK SERVİSLER ---
# İleride buraya istediğin kadar yeni dosya/servis ekleyebilirsin.
SERVICES = [
    {
        "name": "🤖 Python Matrix Botu", 
        "command": [sys.executable, "issue_bot.py"]
    },
    {
        "name": "📊 Otomatik Raporlama Servisi", 
        "command": [sys.executable, "report_generator.py"]
    }
]
def monitor_service(service):
    """Her bir servisi kendi yalıtılmış alanında (thread) izler ve çökerse diriltir."""
    while True:
        print(f"\n[🚀 BAŞLATILIYOR] {service['name']}")
        try:
            # Servisi başlat
            process = subprocess.Popen(service['command'])
            
            # Servis çalıştığı sürece bekle
            process.wait()
            
            # Hata verip kapanırsa buraya düşer
            print(f"\n[⚠️ ÇÖKTÜ] {service['name']} kapandı! 5 saniye içinde yeniden başlatılıyor...")
            time.sleep(5)
            
        except Exception as e:
            print(f"\n[❌ HATA] {service['name']} başlatılırken sorun yaşandı: {e}")
            print("10 saniye sonra tekrar denenecek...")
            time.sleep(10)

if __name__ == "__main__":
    print(f"{'='*50}")
    print("👑 [MASTER SUPERVISOR] SİSTEM ORKESTRASI DEVREDE")
    print(f"{'='*50}")

    threads = []
    
    # Listedeki her bir servis için ayrı bir denetleyici (Thread) başlat
    for svc in SERVICES:
        t = threading.Thread(target=monitor_service, args=(svc,))
        t.daemon = True # Ana kod kapanırsa alt thread'ler de kapansın
        t.start()
        threads.append(t)
        time.sleep(1) # Servislerin aynı anda çakışmaması için 1 saniye bekle

    # Ana programı ayakta tutan sonsuz döngü
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[🛑 SİSTEM] Ana Denetleyici (Master Supervisor) manuel olarak durduruldu.")
        print("Tüm servisler kapatılıyor...")