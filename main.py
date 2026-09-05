import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import time
import requests
from bs4 import BeautifulSoup

# --- ۱. ساخت سرور وب برای زنده نگه داشتن ربات در Render ---
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is active!")

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    server.serve_forever()

threading.Thread(target=run_web_server, daemon=True).start()

# --- ۲. تنظیمات ربات تلگرام ---
TELEGRAM_BOT_TOKEN = "8697938328:AAEsY4xIv6..."  # توکن خودتان
TELEGRAM_CHAT_ID = "6713096570"
THRESHOLD_BUBBLE_PERCENT = -2.0
CHECK_INTERVAL_SECONDS = 300

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        response = requests.post(url, json=payload)
        return response.ok
    except Exception:
        return False

print("Gold Bot is running continuously...")
