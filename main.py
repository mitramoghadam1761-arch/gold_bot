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
        return float(clean_str)
    except Exception:
        return None

def fetch_market_data():
    try:
        url = "https://www.tgju.org/"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            data = {}
            
            # طلای ۱۸ عیار
            el_18k = soup.find('tr', {'data-market-row': 'geram18'}) or soup.find('tr', {'id': 'l-geram18'})
            if el_18k and el_18k.find('td', {'class': 'price'}):
                data['18k'] = parse_price(el_18k.find('td', {'class': 'price'}).text)
                
            # مظنه آب‌شده
            el_mesghal = soup.find('tr', {'data-market-row': 'mesghal'}) or soup.find('tr', {'id': 'l-mesghal'})
            if el_mesghal and el_mesghal.find('td', {'class': 'price'}):
                data['mesghal'] = parse_price(el_mesghal.find('td', {'class': 'price'}).text)
                
            # سکه امامی
            el_coin = soup.find('tr', {'data-market-row': 'sekeb'}) or soup.find('tr', {'id': 'l-sekeb'})
            if el_coin and el_coin.find('td', {'class': 'price'}):
                data['coin'] = parse_price(el_coin.find('td', {'class': 'price'}).text)

            # دلار بازار آزاد
            el_dollar = soup.find('tr', {'data-market-row': 'price_dollar_rl'}) or soup.find('tr', {'id': 'l-price_dollar_rl'})
            if el_dollar and el_dollar.find('td', {'class': 'price'}):
                # تبدیل ریال به تومان
                raw_dollar = parse_price(el_dollar.find('td', {'class': 'price'}).text)
                if raw_dollar:
                    data['dollar'] = raw_dollar / 10 if raw_dollar > 100000 else raw_dollar

            # انس جهانی طلا
            el_ons = soup.find('tr', {'data-market-row': 'ons'}) or soup.find('tr', {'id': 'l-ons'})
            if el_ons and el_ons.find('td', {'class': 'price'}):
                data['ons'] = parse_price(el_ons.find('td', {'class': 'price'}).text)
                
            return data
    except Exception as e:
        print(f"Error fetching market data: {e}")
    return None

def calculate_coin_bubble(coin_price, dollar_price, ons_price):
    """
    محاسبه حباب سکه بر اساس انس جهانی و دلار
    """
    if not coin_price or not dollar_price or not ons_price:
        return None, None
    
    # فرمول ارزش ذاتی سکه کامل (وزن ۷.۹۸۸۰۵ گرم، عیار ۹۰۰ از ۱۰۰۰) + حق ضرب
    intrinsic_value = ((ons_price * dollar_price * 0.900 * 7.98805) / 31.1035) + 50000
    bubble_amount = coin_price - intrinsic_value
    bubble_percent = (bubble_amount / intrinsic_value) * 100
    
    return int(bubble_amount), round(bubble_percent, 2)

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b"Gold & Dollar Analysis Bot is running!")

def bot_loop():
    global last_prices
    print("Gold & Dollar Monitoring loop started...")
    
    send_telegram_message("⚡ <b>ربات هوشمند پایش طلا، سکه و دلار فعال شد.</b>\n"
                          "محاسبه کامل حباب بر اساس دلار و انس جهانی انجام می‌شود.")
    
    first_run = True
    
    while True:
        try:
            market_data = fetch_market_data()
            if market_data and '18k' in market_data:
                p_18k = market_data.get('18k')
                p_mesghal = market_data.get('mesghal')
                p_coin = market_data.get('coin')
                p_dollar = market_data.get('dollar')
                p_ons = market_data.get('ons')
                
                # محاسبه حباب کامل با دلار و انس
                bubble_amt, bubble_pct = calculate_coin_bubble(p_coin, p_dollar, p_ons)
                
                # بررسی نوسان
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
                
                if first_run or should_alert:
                    msg = "📊 <b>تحلیل لحظه‌ای بازار (طلا، سکه و دلار):</b>\n\n"
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
                        msg += f"💡 <b>حباب سکه (بر اساس دلار و انس):</b> {bubble_amt:,.0f} تومان ({bubble_pct}%)\n"
                    
                    send_telegram_message(msg)
                    first_run = False
                
                last_prices['18k'] = p_18k
                last_prices['mesghal'] = p_mesghal
                last_prices['coin'] = p_coin
                last_prices['dollar'] = p_dollar
                
            else:
                print("عدم موفقیت در دریافت داده‌های کامل.")
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
