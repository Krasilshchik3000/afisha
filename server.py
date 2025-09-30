#!/usr/bin/env python3
import http.server
import socketserver
import webbrowser
import os

PORT = 8000

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()

def start_server():
    """Запуск локального веб-сервера"""
    os.chdir('/Users/krasil/Documents/afisha_covers')

    with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
        print(f"Сервер запущен на порту {PORT}")
        print(f"Откройте в браузере: http://localhost:{PORT}/index_selenium.html")

        # Автоматически открываем браузер
        webbrowser.open(f'http://localhost:{PORT}/index_selenium.html')

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nСервер остановлен")
            httpd.shutdown()

if __name__ == "__main__":
    start_server()
