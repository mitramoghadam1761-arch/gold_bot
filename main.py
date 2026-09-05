import os
import time
import threading
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler

# تنظیمات اختصاصی تلگرام
TELEGRAM_BOT_TOKEN = "8697938328:AAEsY4xIv6JP6RYP6SjiSWtnj-57rfEgdss"
TELEGRAM_CHAT_ID = "6713096570"

def send_telegram_message(message):
    """ارسال مستقیم پیام به تلگرام شما"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        print("Telegram response code:", response.status_code)
    except Exception as e:
        print(f"Error sending message to Telegram: {e}")

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b"Gold Bot with Telegram is active!")

def bot_loop():
    print("Gold Bot loop started...")
    # ارسال پیام خوشامدگویی به محض اجرا روی سرور
    send_telegram_message("🤖 ربات پایش قیمت طلا با موفقیت به تلگرام متصل شد و فعال است!")
    
    while True:
        # در این قسمت در آینده کد دریافت قیمت طلا و ارسال آن قرار می‌گیرد
        time.sleep(3600)

def run_http_server():
    port = int(os.environ.get("PORT", 10000))
    print(f"Starting HTTP Server on port {port}...")
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    server.serve_forever()

if __name__ == '__main__':
    bot_thread = threading.Thread(target=bot_loop, daemon=True)
    bot_thread.start()
    
    run_http_server()
