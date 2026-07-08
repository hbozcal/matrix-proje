import asyncio
import aiosqlite
import json
from datetime import datetime
import os

DB_NAME = "bot_state.db"
REPORT_DIR = "raporlar"
HASH_FILE = "processed_images.json"

async def generate_report():
    """Veritabanı ve işlenen benzersiz görsel sayılarını raporlar."""
    if not os.path.exists(REPORT_DIR):
        os.makedirs(REPORT_DIR)

    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d_%H-%M")
    report_filename = f"{REPORT_DIR}/Sistem_Raporu_{date_str}.md"

    print(f"\n[📊 RAPOR] {date_str} için sistem raporu oluşturuluyor...")

    try:
        # --- 1. VERİTABANI İSTATİSTİKLERİ ---
        async with aiosqlite.connect(DB_NAME) as db:
            async with db.execute("SELECT COUNT(id) FROM processed_events") as cursor:
                total_row = await cursor.fetchone()
                total_issues = total_row[0] if total_row else 0

            async with db.execute("SELECT room_id, COUNT(id) FROM processed_events GROUP BY room_id") as cursor:
                room_rows = await cursor.fetchall()

        # --- 2. BENZERSİZ GÖRSEL (HASH) İSTATİSTİKLERİ ---
        unique_image_count = 0
        if os.path.exists(HASH_FILE):
            with open(HASH_FILE, "r") as f:
                try:
                    hashes = json.load(f)
                    unique_image_count = len(hashes)
                except json.JSONDecodeError:
                    pass

        # --- 3. RAPORU YAZDIRMA ---
        with open(report_filename, "w", encoding="utf-8") as f:
            f.write(f"# 📊 Otomasyon Sistemi Analiz Raporu\n\n")
            f.write(f"**Oluşturulma Tarihi:** {now.strftime('%d.%m.%Y %H:%M:%S')}\n\n")
            
            f.write(f"### 🤖 Yapay Zeka & Tasarruf Sistemi\n")
            f.write(f"- **İşlenen Benzersiz Görsel Sayısı:** {unique_image_count}\n")
            f.write(f"- *Not: Sistem aynı görseli ikinci kez analiz etmeyerek token tasarrufu sağlamaktadır.*\n\n")

            f.write(f"### 📈 GitLab İş Kaydı (Issue) İstatistikleri\n")
            f.write(f"- **Toplam Oluşturulan Kayıt:** {total_issues}\n\n")
            
            f.write(f"### 🏢 Odalara Göre Dağılım\n")
            if room_rows:
                for row in room_rows:
                    f.write(f"- **Oda ID:** `{row[0]}` ➔ **{row[1]}** kayıt\n")
            else:
                f.write("- *Henüz sistemde işlenmiş bir kayıt bulunmamaktadır.*\n")

        print(f"[✅ BAŞARILI] Rapor kaydedildi: {report_filename}")
        
    except Exception as e:
        print(f"[❌ HATA] Rapor oluşturulurken sorun yaşandı: {e}")

async def main():
    print("[📈 RAPOR SERVISI] Aktif. Otomatik raporlama ve Mükerrer Görsel denetimi devrede.")
    while True:
        await generate_report()
        await asyncio.sleep(43200) # 12 saatte bir rapor

if __name__ == "__main__":
    asyncio.run(main())