# Simple Overseer to test Phase 3 architecture
import http.server
import socketserver
import json
from urllib.parse import urlparse, parse_qs
import time
import uuid

class OverseerHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.end_headers()
        
        if path == '/' or path == '':
            response = {
                "service": "rika-overseer",
                "version": "3.0.0",
                "status": "online",
                "description": "Policy Gatekeeper",
                "endpoints": ["/health", "/policy", "/check", "/approve"],
                "note": "Simplified version - full dependencies installing"
            }
        elif path == '/health':
            response = {
                "status": "healthy",
                "service": "rika-overseer",
                "version": "3.0.0",
                "port": 5319,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "policy_loaded": True,
                "audit_chain_status": "operational"
            }
        elif path == '/policy':
            response = {
                "version": "1.0.0",
                "capabilities": {
                    "remote_control": {
                        "default": "review",
                        "conditions": {
                            "business_hours_only": True,
                            "max_sessions": 3,
                            "max_duration_minutes": 30
                        }
                    },
                    "model_change": {
                        "default": "review",
                        "conditions": {
                            "require_eval": True,
                            "require_approval": True
                        }
                    },
                    "autonomy_level_change": {
                        "default": "review",
                        "conditions": {
                            "admin_only": True
                        }
                    }
                }
            }
        else:
            response = {"error": "Not found", "path": path}
        
        self.wfile.write(json.dumps(response, indent=2).encode())
    
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length).decode('utf-8')
        
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.end_headers()
        
        try:
            request_data = json.loads(post_data) if post_data else {}
        except:
            request_data = {}
        
        if path == '/check':
            capability = request_data.get('capability', 'unknown')
            requester = request_data.get('requester', 'anonymous')
            
            # Simple policy decisions
            if capability in ['remote_control', 'model_change', 'autonomy_level_change']:
                decision = "review"  # Requires approval
                request_id = f"overseer_{uuid.uuid4().hex[:8]}"
            elif capability in ['data_access', 'safe_refactor']:
                decision = "allow"
                request_id = None
            else:
                decision = "deny"
                request_id = None
            
            response = {
                "decision": decision,
                "reason": f"Default policy for {capability}: {decision}",
                "request_id": request_id,
                "expires_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", 
                                         time.gmtime(time.time() + 300)),  # 5 minutes
                "capability": capability,
                "requester": requester,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            }
            
        elif path == '/approve':
            request_id = request_data.get('request_id', 'unknown')
            approved = request_data.get('approved', False)
            approver = request_data.get('approver', 'system')
            
            response = {
                "status": "processed",
                "request_id": request_id,
                "approved": approved,
                "approver": approver,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "note": "Approval processed by simplified Overseer"
            }
            
        else:
            response = {"error": "Not found", "path": path}
        
        self.wfile.write(json.dumps(response, indent=2).encode())
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.end_headers()
    
    def log_message(self, format, *args):
        pass  # Suppress default logging

def start_overseer():
    PORT = 5319
    
    try:
        with socketserver.TCPServer(("", PORT), OverseerHandler) as httpd:
            print(f"Rika Overseer (Simple) serving at http://localhost:{PORT}")
            print(f"Policy engine: ACTIVE")
            print(f"Audit logging: SIMULATED")
            print(f"n8n integration: CONFIGURED")
            print(f"Press Ctrl+C to stop")
            httpd.serve_forever()
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"ERROR: Port {PORT} is already in use")
        else:
            print(f"ERROR: Error starting Overseer: {e}")

if __name__ == "__main__":
    start_overseer()