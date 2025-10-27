#!/usr/bin/env python3
"""
Simple HTTP server for Rika Atlas UI
Serves static files on port 5173
"""
import http.server
import socketserver
import os
import sys
from pathlib import Path

# Get the directory where this script is located
ui_dir = Path(__file__).parent

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ui_dir), **kwargs)
    
    def end_headers(self):
        # Add CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        super().end_headers()

def main():
    PORT = 5173
    
    print(f"[Atlas UI] Starting server on http://localhost:{PORT}")
    print(f"[Atlas UI] Serving files from: {ui_dir}")
    
    try:
        with socketserver.TCPServer(("", PORT), CustomHTTPRequestHandler) as httpd:
            print(f"[Atlas UI] Server running at http://localhost:{PORT}")
            print(f"[Atlas UI] Press Ctrl+C to stop")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print(f"\n[Atlas UI] Server stopped")
    except OSError as e:
        if e.errno == 10048:  # Port already in use
            print(f"[Atlas UI] ERROR: Port {PORT} is already in use")
            print(f"[Atlas UI] Please stop any existing server on port {PORT}")
        else:
            print(f"[Atlas UI] ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()