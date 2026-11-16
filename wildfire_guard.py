"""
WILDFIRE GUARD — AI-Powered Forest Fire Prevention & Monitoring
Fully self-contained Python application.
Zero external pip dependencies required — uses Python standard library.
Run with:
    python wildfire_guard.py
"""

import http.server
import socketserver
import webbrowser
import os
import threading

PORT = 8050
HTML_FILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html")

class WildfireHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ("/", "/index.html"):
            if os.path.exists(HTML_FILE_PATH):
                with open(HTML_FILE_PATH, "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(content)
            else:
                self.send_response(404)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        return

def run_server():
    server = socketserver.TCPServer(("", PORT), WildfireHandler)
    print(f"🌲 WILDFIRE GUARD Command Center online at http://localhost:{PORT}")
    server.serve_forever()

if __name__ == "__main__":
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    webbrowser.open(f"http://localhost:{PORT}")
    print(f"🌲 WILDFIRE GUARD Dashboard opened in your browser.")
    print("Press Ctrl+C to stop.")
    server_thread.join()
