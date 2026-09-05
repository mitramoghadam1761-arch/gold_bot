import time
import requests
from bs4 import BeautifulSoup

TELEGRAM_BOT_TOKEN = "8697938328:AAEsY4xIv6JP6RYP6SjiSWtnj-57rfEgdss"
TELEGRAM_CHAT_ID = "6713096570"
THRESHOLD_BUBBLE_PERCENT = -2.0
CHECK_INTERVAL_SECONDS = 300

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        response = requests.post(url, json=payload, timeout=10)
        return response.ok
    except Exception:
        return False

def clean_price(price_str):
    if not price_str:
        return None
    cleaned = price_str.replace(',', '').strip()
    try:
        return float(cleaned)
    except ValueError:
        return None

def fetch_tala_ir_data():
    url = "https://www.tala.ir"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        res = requests.get(url, headers=headers, timeout=15)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            mesghal_el = soup.find('td', id='price_mesghal') or soup.find('span', id='price_mesghal')
            dollar_el = soup.find('td', id='price_dollar') or soup.find('span', id='price_dollar')
            ons_el = soup.find('td', id='price_ons') or soup.find('span', id='price_ons')
            
            market_mazneh = clean_price(mesghal_el.text) if mesghal_el else None
            dollar = clean_price(dollar_el.text) if dollar_el else None
            ounce = clean_price(ons_el.text) if ons_el else None
            return ounce, dollar, market_mazneh
    except Exception:
        pass
    return None, None, None

def calculate_bubble(ounce, dollar, market_mazneh):
    theoretical_mazneh = (ounce * dollar) / 9.5742
    bubble_toman = market_mazneh - theoretical_mazneh
    bubble_percent = (bubble_toman / theoretical_mazneh) * 100
    return theoretical_mazneh, bubble_toman, bubble_percent

def main():
    last_alert_time = 0
    while True:
        ounce, dollar, market_mazneh = fetch_tala_ir_data()
        if ounce and dollar and market_mazneh:
            theo_mazneh, bubble_toman, bubble_pct = calculate_bubble(ounce, dollar, market_mazneh)
            if bubble_pct <= THRESHOLD_BUBBLE_PERCENT and (time.time() - last_alert_time > 1800):
                msg = (
                    f"🚨 *فرصت نوسان‌گیری طلا (حباب منفی)* 🚨\n\n"
                    f"📉 *درصد حباب:* `{bubble_pct:.2f}%`\n"
                    f"💰 *ارزان‌تر از واقعیت:* `{abs(bubble_toman):,.0f} تومان`\n\n"
                    f"• مظنه بازار: `{market_mazneh:,.0f}`\n"
                    f"• مظنه تئوریک: `{theo_mazneh:,.0f}`\n"
                    f"• اونس: `${ounce:,.2f}` | دلار: `{dollar:,.0f}`"
                )
                if send_telegram_alert(msg):
                    last_alert_time = time.time()
        time.sleep(CHECK_INTERVAL_SECONDS)

if __name__ == "__main__":
    main()
