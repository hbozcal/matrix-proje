import aiosqlite

import config

DB_NAME = config.DB_NAME


async def init_db():
    """Botun durumunu saklayacağı veritabanını ve tabloları hazırlar."""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS processed_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                matrix_event_id TEXT UNIQUE,
                gitlab_issue_iid INTEGER,
                room_id TEXT,
                created_at TEXT
            )
        """)
        await db.commit()
    print("[🗄️ VERİTABANI] SQLite veritabanı aktif ve tablolar doğrulandı.")


async def get_issue_by_event(matrix_event_id: str):
    """Bir mesajın daha önce işlenip işlenmediğini kontrol eder.
    İşlendiyse GitLab Issue numarasını döner, işlenmediyse None döner."""
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute(
            "SELECT gitlab_issue_iid FROM processed_events WHERE matrix_event_id = ?",
            (matrix_event_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None


async def save_processed_event(matrix_event_id: str, gitlab_issue_iid: int, room_id: str, created_at: str):
    """Başarıyla oluşturulan iş kaydını veritabanına işler (Mükerrerliği önlemek için)."""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT INTO processed_events (matrix_event_id, gitlab_issue_iid, room_id, created_at) VALUES (?, ?, ?, ?)",
            (matrix_event_id, gitlab_issue_iid, room_id, created_at)
        )
        await db.commit()
    print(f"[🗄️ VERİTABANI] {matrix_event_id} mesajı için #{gitlab_issue_iid} kaydı hafızaya alındı.")


async def get_latest_issue_by_room(room_id: str):
    """Verilen oda ID'sinde açılmış en son GitLab Issue numarasını döner."""
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute(
            "SELECT gitlab_issue_iid FROM processed_events WHERE room_id = ? ORDER BY id DESC LIMIT 1",
            (room_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None
