# Simple L2 Autonomy Controller to test Phase 3 architecture
import http.server
import socketserver
import json
from urllib.parse import urlparse
import time
import uuid

class L2AutonomyHandler(http.server.BaseHTTPRequestHandler):
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
                "service": "rika-l2-autonomy",
                "version": "3.0.0",
                "status": "online",
                "description": "Guarded Autonomy L2 System",
                "endpoints": ["/health", "/status", "/set-level", "/request-action", "/execute-task"],
                "note": "Simplified version - full dependencies installing"
            }
        elif path == '/health':
            response = {
                "status": "healthy",
                "service": "rika-l2-autonomy",
                "version": "3.0.0",
                "port": 5322,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "autonomy_level": "l2_guarded",
                "active_tasks": 0
            }
        elif path == '/status':
            response = {
                "autonomy_level": "l2_guarded",
                "bounds": {
                    "allowed_scopes": ["safe_refactor", "ui_improvement", "performance"],
                    "max_files_per_change": 5,
                    "max_lines_per_file": 100,
                    "require_tests": True,
                    "require_eval_pass": True
                },
                "active_tasks": {},
                "available_agents": ["scout-v0", "craft-v0"],
                "overseer_connection": "connected",
                "sage_connection": "connected",
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            }
        elif path.startswith('/task/'):
            task_id = path.split('/')[-1]
            response = {
                "request_id": task_id,
                "status": "completed",
                "agent_id": "scout-v0",
                "start_time": "2025-09-09T23:30:00Z",
                "end_time": "2025-09-09T23:32:00Z",
                "files_changed": ["example/file1.py", "example/file2.py"],
                "eval_results": {
                    "passed": True,
                    "score": 0.92,
                    "issues": []
                },
                "error": None
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
        
        if path == '/set-level':
            level = request_data.get('level', 'disabled')
            
            response = {
                "status": "success",
                "new_level": level,
                "previous_level": "disabled",
                "overseer_approval": "granted",
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            }
            
        elif path == '/request-action':
            task_description = request_data.get('task_description', 'Unknown task')
            scope = request_data.get('scope', 'safe_refactor')
            priority = request_data.get('priority', 'normal')
            
            # Simulate policy decision
            if scope in ['safe_refactor', 'ui_improvement', 'performance']:
                approved = True
                reason = f"Approved for L2 autonomy within bounds"
                request_id = f"l2_{uuid.uuid4().hex[:8]}"
            else:
                approved = False
                reason = f"Scope {scope} requires higher approval level"
                request_id = None
            
            response = {
                "request_id": request_id,
                "approved": approved,
                "reason": reason,
                "bounds": {
                    "max_files": 5,
                    "max_lines_per_file": 100,
                    "require_tests": True,
                    "require_eval": True
                } if approved else None,
                "expires_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", 
                                         time.gmtime(time.time() + 1800)),  # 30 minutes
                "restrictions": [
                    f"Scope limited to: {scope}",
                    "Max files: 5",
                    "Max lines per file: 100"
                ] if approved else []
            }
            
        elif path == '/execute-task':
            task_description = request_data.get('task_description', 'Unknown task')
            scope = request_data.get('scope', 'safe_refactor')
            
            # Simulate task execution
            request_id = f"l2_{uuid.uuid4().hex[:8]}"
            
            response = {
                "request_id": request_id,
                "status": "completed",
                "agent_id": "craft-v0",
                "start_time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "files_changed": [
                    "phase2.5/core/api.py",
                    "phase2.5/ui/src/components/Dashboard.tsx"
                ],
                "eval_results": {
                    "passed": True,
                    "metrics": {
                        "accuracy": 0.94,
                        "performance_impact": "positive",
                        "test_coverage": 0.89
                    }
                },
                "rollback_info": None,
                "error": None,
                "note": "Task completed successfully within L2 bounds"
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
        pass

def start_l2_autonomy():
    PORT = 5322
    
    try:
        with socketserver.TCPServer(("", PORT), L2AutonomyHandler) as httpd:
            print(f"Rika L2 Autonomy (Simple) serving at http://localhost:{PORT}")
            print(f"Autonomy level: L2_GUARDED")
            print(f"Agents: scout-v0, craft-v0")
            print(f"Bounds: safe_refactor, ui_improvement, performance")
            print(f"Press Ctrl+C to stop")
            httpd.serve_forever()
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"ERROR: Port {PORT} is already in use")
        else:
            print(f"ERROR: Error starting L2 Autonomy: {e}")

if __name__ == "__main__":
    start_l2_autonomy()