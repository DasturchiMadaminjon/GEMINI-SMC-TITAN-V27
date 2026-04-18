import os, json, sys, threading, queue
from urllib.parse import urlparse, parse_qs
from http.server import HTTPServer, BaseHTTPRequestHandler

# Add current directory to sys.path for modular imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import shared utilities and constants
from handlers.utils import (
    PORT, HOME, log, ThreadingHTTPServer, cors, send_json, 
    rate_limit, sse_push, sse_done, handle_sse, unquote
)

# Import modular handlers
from handlers.ai_handler import handle_ai
from handlers.file_handler import handle_file_get, handle_file_post
from handlers.system_handler import handle_system
from handlers.media_handler import handle_media, handle_media_get
from handlers.utility_handler import handle_util_get, handle_util_post
from handlers.complex_handler import handle_complex_post

# --- MODULAR FRONTEND LOADING ---
template_path = os.path.join(os.path.dirname(__file__), 'templates', 'index.html')
try:
    with open(template_path, 'r', encoding='utf-8') as f:
        HTML = f.read()
except Exception as e:
    HTML = f'<html><body><h1>Error loading template</h1><p>{str(e)}</p></body></html>'
# --------------------------------

class H(BaseHTTPRequestHandler):
    def send_json(self, data, code=200):
        send_json(self, data, code)

    def do_OPTIONS(self):
        self.send_response(200)
        cors(self)
        self.end_headers()

    def do_GET(self):
        path = self.path
        if path.startswith("/api/"): path = path[4:]
        p = urlparse(path)
        qs = parse_qs(p.query)

        # Static / UI
        if p.path in ("/", "/index.html"):
            b = HTML.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html;charset=utf-8")
            self.send_header("Content-Length", str(len(b)))
            self.end_headers()
            self.wfile.write(b)
            return

        # Delegate to utility GET handlers (home, deps, voices)
        if handle_util_get(self, p.path, qs): return

        # Delegate to file GET handlers (list, read)
        if handle_file_get(self, p.path, qs): return

        # Delegate to media GET handlers (streaming)
        if handle_media_get(self, p.path, qs): return

        # Delegate to SSE handler
        if p.path == "/sse":
            return handle_sse(self, qs)

        self.send_json({"error": "Topilmadi"}, 404)

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        try:
            body = json.loads(self.rfile.read(n)) if n else {}
        except:
            return self.send_json({"error": "Noto'g'ri JSON"}, 400)
        
        path = self.path
        if path.startswith("/api/"): path = path[4:]
        p = urlparse(path).path

        # 1. AI Handlers
        if handle_ai(self, p, body): return

        # 2. File Handlers
        if handle_file_post(self, p, body): return

        # 3. System Handlers
        if handle_system(self, p, body): return

        # 4. Media Handlers
        if handle_media(self, p, body): return

        # 5. Utility Handlers
        if handle_util_post(self, p, body): return

        # 6. Complex Handlers
        if handle_complex_post(self, p, body): return

        self.send_json({"error": "Noma'lum endpoint"}, 404)

if __name__ == "__main__":
    print("=" * 52)
    print("  Universal File Analyzer v5 (MODULAR)")
    print(f"  >>> http://127.0.0.1:{PORT} <<<")
    print("=" * 52)
    
    server = ThreadingHTTPServer(("127.0.0.1", PORT), H)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nTo'xtatildi.")