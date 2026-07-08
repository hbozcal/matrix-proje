import time
from datetime import timezone, timedelta

# --- MATRIX AYARLARI ---
HOMESERVER = "http://localhost:8008"
BOT_USER = "@gitlab-bot:localhost"
BOT_TOKEN = "syt_Z2l0bGFiLWJvdA_nmPnxFaOotBZMABBZpZc_3QxPVx"
ALLOWED_ROOM_NAMES = ["Üretim", "üretim", "Yazılım", "yazılım", "YAZILIM", "Uretim_Test"]

# --- GITLAB AYARLARI ---
GITLAB_URL = "https://gitlab.com" 
GITLAB_PROJECT_ID = "83126217" 
GITLAB_TOKEN = "glpat-c0vhEv5sjRisdnqGIK1Qj2M6MQpvOjEKdTpuOHN1bA8.01.1719eb39r" 

# --- CLAUDE AI AYARI ---
ANTHROPIC_API_KEY = "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"

# --- OPENAI AI AYARI (🎙️ Sesli Mesaj Deşifresi İçin Yeni Eklendi) ---
OPENAI_API_KEY = 

# --- ZAMAN VE CÜZDAN KORUMA KALKANI ---
TZ_TURKEY = timezone(timedelta(hours=3))
BOT_START_TIME = int(time.time() * 1000)

# --- NODE.JS WEBHOOK ---
WEBHOOK_URL = "http://localhost:3000/api/v1/messages"