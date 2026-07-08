import subprocess
import time
import sys

# Denetlenecek ana bot dosyamız
BOT_SCRIPT = "issue_bot.py"

def run_bot():
    while True:
        print(f"\n[👀 GÖZLEMCİ] {BOT_SCRIPT} başlatılıyor...")
        
        try:
            # Botu alt bir işlem (subprocess) olarak başlat
            # sys.executable, sistemdeki aktif Python yolunu (python veya python3) otomatik bulur
            process = subprocess.Popen([sys.executable, BOT_SCRIPT])
            
            # Bot çalıştığı sürece gözlemci burada bekler
            process.wait() 
            
            # Eğer kod buraya ulaştıysa, bot bir sebepten çökmüş veya kapanmıştır
            print(f"\n[⚠️ UYARI] Bot beklenmedik şekilde kapandı! (Çıkış Kodu: {process.returncode})")
            print("[🔄 YENİDEN BAŞLATMA] Sistem 5 saniye içinde otomatik olarak yeniden ayağa kaldırılacak...")
            time.sleep(5)
            
        except KeyboardInterrupt:
            # Sen terminalde CTRL+C yaparsan gözlemci döngüyü kırıp tamamen durur
            print("\n[🛑 GÖZLEMCİ] Sistem manuel olarak kapatıldı. Denetim sonlandırılıyor.")
            break
            
        except Exception as e:
            print(f"\n[❌ KRİTİK HATA] Gözlemci botu başlatırken bir sorun yaşadı: {e}")
            print("10 saniye sonra tekrar denenecek...")
            time.sleep(10)

if __name__ == "__main__":
    print(f"{'='*50}")
    print("[🛡️ SİSTEM] Gözlemci (Watchdog) Kalkanı Devrede!")
    print(f"[🛡️ SİSTEM] {BOT_SCRIPT} 7/24 denetlenecek ve çökerse diriltilecek.")
    print(f"{'='*50}")
    run_bot()