import os, json, shutil, base64, mimetypes, urllib.request, subprocess, sys, tempfile, platform, zipfile, sqlite3, re
import threading, logging, time, queue
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, unquote
from socketserver import ThreadingMixIn

# Load environment variables
try:
    from dotenv import load_dotenv
    dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path)
except ImportError:
    pass

class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True

# --- CONFIGURATION ---
PORT = int(os.environ.get("BRIDGE_PORT", 57845))
HOME = str(Path.home())
_raw_roots = os.environ.get("ALLOWED_ROOTS", "USER_HOME,TEMP_DIR,C:\\,D:\\").split(",")

ALLOWED_ROOTS = []
for r in _raw_roots:
    r = r.strip()
    if not r: continue
    if r == "USER_HOME": ALLOWED_ROOTS.append(HOME)
    elif r == "TEMP_DIR": ALLOWED_ROOTS.append(tempfile.gettempdir())
    else: ALLOWED_ROOTS.append(r)
# ---------------------

# ── Logger ────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.WARNING,
                    format="%(asctime)s [%(levelname)s] %(name)s %(message)s",
                    handlers=[
                        logging.FileHandler(os.path.join(HOME, ".analyzer.log"), encoding="utf-8"),
                    ])
log = logging.getLogger("analyzer")
log.setLevel(logging.DEBUG)

import traceback as _tb
def _log_uncaught(exc_type, exc_val, exc_tb):
    log.error("Unhandled exception: %s", "".join(_tb.format_exception(exc_type, exc_val, exc_tb)))

sys.excepthook = _log_uncaught

# ── Rate Limiter ──────────────────────────────────────────────────────────
import collections
_rl_counts = collections.defaultdict(list)
_rl_lock = threading.Lock()

def rate_limit(key, max_calls, period):
    now = time.time()
    with _rl_lock:
        times = _rl_counts[key]
        _rl_counts[key] = [t for t in times if now - t < period]
        if len(_rl_counts[key]) >= max_calls:
            return False
        _rl_counts[key].append(now)
        return True

# ── SSE progress queues ───────────────────────────────────────────────────
_sse_queues = {}
def sse_push(task_id, data):
    if task_id in _sse_queues: _sse_queues[task_id].put(data)
def sse_done(task_id):
    if task_id in _sse_queues: _sse_queues[task_id].put(None)

def handle_sse(h, qs):
    tid = qs.get("id", [""])[0]
    if not tid: 
        send_json(h, {"error": "id kerak"}, 400)
        return True
    
    q = queue.Queue()
    _sse_queues[tid] = q
    h.send_response(200)
    h.send_header("Content-Type", "text/event-stream")
    h.send_header("Cache-Control", "no-cache")
    h.send_header("Connection", "keep-alive")
    cors(h)
    h.end_headers()
    try:
        while True:
            msg = q.get(timeout=60) # Increased timeout
            if msg is None:
                h.wfile.write(b"data: {\"done\":true}\n\n")
                break
            h.wfile.write(f"data: {json.dumps(msg)}\n\n".encode())
            h.wfile.flush()
    except Exception as e:
        log.error(f"SSE error for {tid}: {e}")
    finally:
        _sse_queues.pop(tid, None)
    return True

# ── Path security ─────────────────────────────────────────────────────────
def is_safe_path(path):
    try:
        r = str(Path(path).resolve())
        for root in ALLOWED_ROOTS:
            res_root = str(Path(root).resolve())
            if r.startswith(res_root):
                return True
        return False
    except Exception as e:
        log.error(f"Path safety check error: {e}")
        return False

def safe_path(path):
    try:
        resolved = str(Path(path).resolve())
    except Exception:
        raise ValueError(f"Yaroqsiz yo'l: {path}")
    if not is_safe_path(resolved):
        raise PermissionError(f"Taqiqlangan: {resolved}")
    return resolved

# ── Dependency checker ────────────────────────────────────────────────────
_dep_cache = None
def check_deps():
    global _dep_cache
    if _dep_cache is not None: return _dep_cache
    res = {}
    for tool in ["ffmpeg", "git", "node", "docker", "tesseract"]:
        try:
            subprocess.run([tool, "--version"], capture_output=True, timeout=2,
                           stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL); res[tool] = True
        except:
            res[tool] = False
    _dep_checks = [("edge_tts", "edge_tts"), ("google-generativeai", "google.generativeai"),
                    ("openpyxl", "openpyxl"), ("python-docx", "docx"), ("pypdf", "pypdf"),
                    ("Pillow", "PIL"), ("cryptography", "cryptography"),
                    ("pytesseract", "pytesseract"), ("qrcode", "qrcode"), ("fpdf2", "fpdf")]
    for pkg, imp in _dep_checks:
        try:
            __import__(imp); res[pkg] = True
        except ImportError:
            res[pkg] = False
    _dep_cache = res
    return res

try:
    import google.generativeai as genai; HAS_GENAI = True
except:
    HAS_GENAI = False

def cors(h):
    h.send_header("Access-Control-Allow-Origin", "*")
    h.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
    h.send_header("Access-Control-Allow-Headers", "Content-Type,Range")

def send_json(h, data, code=200):
    b = json.dumps(data, ensure_ascii=False).encode()
    h.send_response(code)
    h.send_header("Content-Type", "application/json;charset=utf-8")
    cors(h)
    h.send_header("Content-Length", str(len(b)))
    h.end_headers()
    h.wfile.write(b)
