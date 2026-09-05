import os
import time
import threading
import requests
from bs4 import BeautifulSoup
from http.server import HTTPServer, BaseHTTPRequestHandler

TELEGRAM_BOT_TOKEN = "8697938328:AAEsY4xIv6JP6RYP6SjiSWtnj-57rfEgdss"
TELEGRAM_CHAT_ID = "6713096570"

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Error sending message to Telegram: {e}")

def fetch_gold_prices():
    try:
        url = "https://www.tgju.org/"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            prices = {}
            
            item_18k = soup.find('tr', {'id': 'l-geram18'})
            if item_18k:
                val = item_18k.find('td', {'class': 'price'}).text
                prices['18k'] = val.strip()
                
            item_mesghal = soup.find('tr', {'id': 'l-mesghal'})
            if item_mesghal:
                val = item_mesghal.find('td', {'class': 'price'}).text
                prices['mesghal'] = val.strip()
                
            return prices
    except Exception as e:
        print(f"Error scraping prices: {e}")
    return None

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b"Gold Monitoring Bot is active!")

def bot_loop():
    print("Gold Bot monitoring loop started...")
    send_telegram_message("🤖 ربات پایش دقیق طلا فعال شد و هر ۱ دقیقه بازار را رصد می‌کند.")
    
    while True:
        try:
            prices = fetch_gold_prices()
            if prices:
                msg = "📊 <b>گزارش لحظه‌ای بازار طلا:</b>\n\n"
                if '18k' in prices:
                    msg += f"🔹 طلای ۱۸ عیار: <code>{prices['18k']}</code> تومان\n"
                if 'mesghal' in prices:
                    msg += f"🔸 مظنه آب‌شده: <code>{prices['mesghal']}</code> تومان\n"
                
                send_telegram_message(msg)
            else:
                print("امکان دریافت قیمت‌ها در این چرخه وجود نداشت.")
        except Exception as e:
            print(f"Error in loop: {e}")
            
        time.sleep(60)

def run_http_server():
    port = int(os.environ.get("PORT", 10000))
    print(f"Starting HTTP Server on port {port}...")
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    server.serve_forever()

if __name__ == '__main__':
    bot_thread = threading.Thread(target=bot_loop, daemon=True)
    bot_thread.start()
    
    run_http_server()
