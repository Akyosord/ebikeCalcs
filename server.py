"""
Simple HTTP server for the E-Bike Acceleration Simulator.
Serves the HTML app and provides API endpoints to save/load bike data as JSON.
"""

import http.server
import json
import os
import webbrowser
from pathlib import Path

PORT = 8080
DATA_FILE = Path(__file__).parent / "bikes_data.json"


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(Path(__file__).parent), **kwargs)

    def do_GET(self):
        if self.path == '/api/load':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            if DATA_FILE.exists():
                data = DATA_FILE.read_text(encoding='utf-8')
            else:
                data = '[]'
            self.wfile.write(data.encode('utf-8'))
        elif self.path == '/' or self.path == '':
            self.path = '/index.html'
            super().do_GET()
        else:
            super().do_GET()

    def do_POST(self):
        if self.path == '/api/save':
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > 10_000_000:  # 10MB limit
                self.send_response(413)
                self.end_headers()
                return
            body = self.rfile.read(content_length)
            try:
                data = json.loads(body)
                DATA_FILE.write_text(json.dumps(data, indent=2), encoding='utf-8')
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(b'{"ok":true}')
            except (json.JSONDecodeError, OSError) as e:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def log_message(self, format, *args):
        # Quieter logging - suppress API and favicon noise
        try:
            msg = str(args[0]) if args else ''
            if '/api/' in msg or 'favicon' in msg:
                return
        except Exception:
            pass
        super().log_message(format, *args)


def main():
    server = http.server.HTTPServer(('127.0.0.1', PORT), Handler)
    url = f'http://localhost:{PORT}'
    print(f"E-Bike Simulator running at {url}")
    print(f"Data saves to: {DATA_FILE}")
    print("Press Ctrl+C to stop.\n")
    webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
        server.server_close()


if __name__ == '__main__':
    main()
