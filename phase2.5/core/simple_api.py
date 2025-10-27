# Simple API to get localhost:5317 working while dependencies install
import http.server
import socketserver
import json
from urllib.parse import urlparse
import threading
import time

class RikaAPIHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        if path == '/' or path == '':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', '*')
            self.end_headers()
            
            root_data = {
                "service": "rika-core-api",
                "version": "2.5.0",
                "status": "online",
                "endpoints": [
                    "/health",
                    "/selfcheck",
                    "/docs (not available in simple mode)"
                ],
                "note": "Simplified API running - full version installing dependencies"
            }
            self.wfile.write(json.dumps(root_data).encode())
            
        elif path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', '*')
            self.end_headers()
            
            health_data = {
                "status": "healthy",
                "service": "rika-core-api",
                "version": "2.5.0",
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "note": "Simplified API - full dependencies installing"
            }
            self.wfile.write(json.dumps(health_data).encode())
            
        elif path == '/selfcheck':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', '*')
            self.end_headers()
            
            selfcheck_data = {
                "api": {"status": "online", "port": 5317},
                "database": {"status": "checking", "note": "Full API loading"},
                "nats": {"status": "checking", "note": "Full API loading"},
                "livekit": {"status": "configured", "url": "wss://rika-marzcsys.livekit.cloud"},
                "overall": "dependencies_installing",
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            }
            self.wfile.write(json.dumps(selfcheck_data).encode())
            
        else:
            self.send_response(404)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            error_data = {"error": "Not found", "path": path}
            self.wfile.write(json.dumps(error_data).encode())
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.end_headers()
    
    def log_message(self, format, *args):
        # Suppress default logging
        pass

def start_simple_api():
    PORT = 5317
    
    try:
        with socketserver.TCPServer(("", PORT), RikaAPIHandler) as httpd:
            print(f"Simple Rika API serving at http://localhost:{PORT}")
            print(f"Health endpoint: http://localhost:{PORT}/health")
            print(f"Selfcheck endpoint: http://localhost:{PORT}/selfcheck")
            print(f"Full API with dependencies will replace this when ready")
            print(f"Press Ctrl+C to stop")
            httpd.serve_forever()
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"ERROR: Port {PORT} is already in use")
        else:
            print(f"ERROR: Error starting server: {e}")

if __name__ == "__main__":
    start_simple_api()