import os
import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b"Gold Bot is active!")

def bot_loop():
    print("Gold Bot loop started...")
    while True:
        # کد اصلی بررسی قیمت طلا
        time.sleep(60)

def run_http_server():
    port = int(os.environ.get("PORT", 10000))
    print(f"Starting HTTP Server on port {port}...")
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    server.serve_forever()

if __name__ == '__main__':
    # اجرای حلقه ربات در پس‌زمینه
    bot_thread = threading.Thread(target=bot_loop, daemon=True)
    bot_thread.start()
    
    # اجرای وب‌سرور در ترد اصلی جهت زنده و فعال نگه داشتن برنامه
    run_http_server()
