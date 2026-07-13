"""
Uygulama yapılandırması.
Tüm secret/ortam-bağımlı değerler .env dosyasından okunur.
Kod içinde ASLA gerçek token/anahtar bulunmamalıdır.
"""
import os
import sys
import time
from datetime import timezone, timedelta

from dotenv import load_dotenv

load_dotenv()


def _require(name: str) -> str:
    """Zorunlu bir env değişkenini okur; yoksa programı net bir hatayla durdurur."""
    value = os.environ.get(name)
    if not value:
        sys.exit(f"[❌ CONFIG HATASI] Zorunlu ortam değişkeni eksik: {name}. .env dosyanı kontrol et.")
    return value


# --- MATRIX AYARLARI ---
HOMESERVER = os.environ.get("MATRIX_SERVER", "http://localhost:8008")
BOT_USER = _require("MATRIX_USER")
BOT_TOKEN = _require("MATRIX_ACCESS_TOKEN")

_allowed_rooms_raw = os.environ.get(
    "ALLOWED_ROOM_NAMES",
    "Üretim,üretim,Yazılım,yazılım,YAZILIM,Uretim_Test",
)
ALLOWED_ROOM_NAMES = [r.strip() for r in _allowed_rooms_raw.split(",") if r.strip()]

# --- GITLAB AYARLARI ---
GITLAB_URL = os.environ.get("GITLAB_URL", "https://gitlab.com")
GITLAB_PROJECT_ID = _require("GITLAB_PROJECT_ID")
GITLAB_TOKEN = _require("GITLAB_TOKEN")

# --- CLAUDE AI AYARI ---
ANTHROPIC_API_KEY = _require("CLAUDE_API_KEY")

# --- OPENAI AI AYARI (Sesli Mesaj Deşifresi İçin) ---
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

# --- WHISPER / FFMPEG (yerel ses deşifre motoru) ---
FFMPEG_PATH = os.environ.get("FFMPEG_PATH", "")  # boşsa PATH değişikliği yapılmaz
WHISPER_MODEL = os.environ.get("WHISPER_MODEL", "base")
WHISPER_LANGUAGE = os.environ.get("WHISPER_LANGUAGE", "tr")

# --- ZAMAN VE ÇALIŞMA AYARLARI ---
TZ_TURKEY = timezone(timedelta(hours=int(os.environ.get("TZ_OFFSET_HOURS", "3"))))
BOT_START_TIME = int(time.time() * 1000)

# --- NODE.JS WEBHOOK ---
WEBHOOK_URL = os.environ.get("NODEJS_WEBHOOK_URL", "http://localhost:3000/api/v1/messages")

# --- VERİTABANI ---
DB_NAME = os.environ.get("DB_NAME", "bot_state.db")

# --- LOGLAMA ---
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
