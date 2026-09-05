import os
import time
import threading
import requests
from bs4 import BeautifulSoup
from http.server import HTTPServer, BaseHTTPRequestHandler

TELEGRAM_BOT_TOKEN = "8697938328:AAEsY4xIv6JP6RYP6SjiSWtnj-57rfEgdss"
TELEGRAM_CHAT_ID = "6713096570"

# حد آستانه هشدار نوسان (به درصد)
ALERT_PERCENT_THRESHOLD = 0.5

last_prices = {
    '18k': None,
    'mesghal': None,
    'coin': None,
    'dollar': None
}

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

def parse_price(price_str):
    if not price_str:
        return None
    try:
        clean_str = ''.join(c for c in price_str if c.isdigit())
        return float(clean_str) if clean_str else None
    except Exception:
        return None

def fetch_market_data():
    data = {}
    try:
        url = "https://www.tgju.org/"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 1. طلای 18 عیار
            el_18k = soup.find('tr', {'data-market-row': 'geram18'}) or soup.find('tr', {'id': 'l-geram18'})
            if el_18k:
                p_td = el_18k.find('td', {'class': 'price'})
                if p_td:
                    data['18k'] = parse_price(p_td.text)
                
            # 2. مظنه آب‌شده
            el_mesghal = soup.find('tr', {'data-market-row': 'mesghal'}) or soup.find('tr', {'id': 'l-mesghal'})
            if el_mesghal:
                p_td = el_mesghal.find('td', {'class': 'price'})
                if p_td:
                    data['mesghal'] = parse_price(p_td.text)
                
            # 3. سکه امامی
            el_coin = soup.find('tr', {'data-market-row': 'sekeb'}) or soup.find('tr', {'id': 'l-sekeb'})
            if el_coin:
                p_td = el_coin.find('td', {'class': 'price'})
                if p_td:
                    data['coin'] = parse_price(p_td.text)

            # 4. دلار بازار آزاد
            el_dollar = soup.find('tr', {'data-market-row': 'price_dollar_rl'}) or soup.find('tr', {'id': 'l-price_dollar_rl'})
            if el_dollar:
                p_td = el_dollar.find('td', {'class': 'price'})
                if p_td:
                    raw_dollar = parse_price(p_td.text)
                    if raw_dollar:
                        data['dollar'] = raw_dollar / 10 if raw_dollar > 100000 else raw_dollar

            # 5. انس جهانی طلا
            el_ons = soup.find('tr', {'data-market-row': 'ons'}) or soup.find('tr', {'id': 'l-ons'})
            if el_ons:
                p_td = el_ons.find('td', {'class': 'price'})
                if p_td:
                    data['ons'] = parse_price(p_td.text)
                    
    except Exception as e:
        print(f"Error fetching market data: {e}")
        
    return data

def calculate_coin_bubble(coin_price, dollar_price, ons_price):
    if not coin_price or not dollar_price or not ons_price:
        return None, None
    
    try:
        intrinsic_value = ((ons_price * dollar_price * 0.900 * 7.98805) / 31.1035) + 50000
        bubble_amount = coin_price - intrinsic_value
        bubble_percent = (bubble_amount / intrinsic_value) * 100
        return int(bubble_amount), round(bubble_percent, 2)
    except Exception:
        return None, None

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b"Gold & Dollar Analysis Bot is running stably!")

def bot_loop():
    global last_prices
    print("Gold & Dollar Monitoring loop started...")
    
    first_run = True
    
    while True:
        try:
            market_data = fetch_market_data()
            p_18k = market_data.get('18k')
            p_mesghal = market_data.get('mesghal')
            p_coin = market_data.get('coin')
            p_dollar = market_data.get('dollar')
            p_ons = market_data.get('ons')
            
            # بررسی دریافت حداقل یکی از شاخص‌ها
            if p_18k or p_mesghal or p_coin or p_dollar:
                
                bubble_amt, bubble_pct = calculate_coin_bubble(p_coin, p_dollar, p_ons)
                
                should_alert = False
                alert_reasons = []
                
                if not first_run:
                    if last_prices['18k'] and p_18k:
                        chg = ((p_18k - last_prices['18k']) / last_prices['18k']) * 100
                        if abs(chg) >= ALERT_PERCENT_THRESHOLD:
                            should_alert = True
                            d = "📈 افزایش" if chg > 0 else "📉 کاهش"
                            alert_reasons.append(f"{d} {abs(chg):.2f}٪ در طلای ۱۸ عیار")
                    
                    if last_prices['dollar'] and p_dollar:
                        chg_d = ((p_dollar - last_prices['dollar']) / last_prices['dollar']) * 100
                        if abs(chg_d) >= ALERT_PERCENT_THRESHOLD:
                            should_alert = True
                            d = "📈 افزایش" if chg_d > 0 else "📉 کاهش"
                            alert_reasons.append(f"{d} {abs(chg_d):.2f}٪ در نرخ دلار")
                
                # ارسال گزارش در اولین اجرا یا زمان بروز نوسان
                if first_run or should_alert:
                    msg = "📊 <b>گزارش تحلیلی بازار (طلا، سکه و دلار):</b>\n\n"
                    if alert_reasons:
                        msg += "🚨 <b>هشدار نوسان بازار:</b>\n" + "\n".join(alert_reasons) + "\n\n"
                        
                    if p_dollar:
                        msg += f"💵 <b>دلار آزاد:</b> {p_dollar:,.0f} تومان\n"
                    if p_18k:
                        msg += f"🔹 <b>طلای ۱۸ عیار:</b> {p_18k:,.0f} تومان\n"
                    if p_mesghal:
                        msg += f"🔸 <b>مظنه آب‌شده:</b> {p_mesghal:,.0f} تومان\n"
                    if p_coin:
                        msg += f"🥇 <b>سکه امامی:</b> {p_coin:,.0f} تومان\n"
                    if bubble_amt is not None:
                        msg += f"💡 <b>حباب سکه:</b> {bubble_amt:,.0f} تومان ({bubble_pct}%)\n"
                    
                    send_telegram_message(msg)
                    first_run = False
                
                # ذخیره آخرین قیمت‌ها
                if p_18k: last_prices['18k'] = p_18k
                if p_mesghal: last_prices['mesghal'] = p_mesghal
                if p_coin: last_prices['coin'] = p_coin
                if p_dollar: last_prices['dollar'] = p_dollar
                
            else:
                print("عدم دریافت داده در این نوبت.")
        except Exception as e:
            print(f"Error in bot loop: {e}")
            
        time.sleep(60)

def run_http_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    server.serve_forever()

if __name__ == '__main__':
    bot_thread = threading.Thread(target=bot_loop, daemon=True)
    bot_thread.start()
    
    run_http_server()
