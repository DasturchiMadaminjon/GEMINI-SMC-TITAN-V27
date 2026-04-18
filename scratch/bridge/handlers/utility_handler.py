import subprocess, os, json, sys, tempfile, threading, base64, sqlite3
from pathlib import Path
from handlers.utils import log, send_json, HOME, sse_push, sse_done, safe_path, HAS_GENAI, check_deps

def handle_util_get(h, p, qs):
    if p == "/home":
        return send_json(h, {"home": HOME, "sep": os.sep, "has_genai": HAS_GENAI})

    if p == "/deps":
        return send_json(h, {"deps": check_deps()})

    if p == "/tts_voices":
        try:
            result = subprocess.run([sys.executable, "-m", "edge_tts", "--list-voices"], capture_output=True, text=True, timeout=15)
            if result.returncode != 0: return send_json(h, {"error": "edge-tts hato berdi"})
            voices = [line.split()[0] for line in result.stdout.strip().split("\n") if line.strip() and not line.startswith("Name") and not line.startswith("---")]
            return send_json(h, {"voices": voices})
        except Exception as e: return send_json(h, {"error": str(e)}, 500)

    return False

def handle_util_post(h, p, body):
    if p == "/tts":
        out_path = None
        try:
            text = body.get("text", ""); voice = body.get("voice", "uz-UZ-MadinaNeural"); rate = body.get("rate", "+0%"); task_id = body.get("task_id", "")
            import uuid as _uuid; out_path = str(Path(tempfile.gettempdir()) / f"tts_{_uuid.uuid4().hex}.mp3")
            def run_tts():
                if task_id: sse_push(task_id, {"progress": 20, "msg": "TTS boshlandi..."})
                res = subprocess.run([sys.executable, "-m", "edge_tts", "--voice", voice, "--rate", rate, "--text", text, "--write-media", out_path], capture_output=True, text=True, timeout=60)
                if res.returncode != 0:
                    if task_id: sse_push(task_id, {"progress": -1, "msg": "edge-tts xato", "ok": False}); sse_done(task_id)
                    return
                with open(out_path, "rb") as f: data = base64.b64encode(f.read()).decode()
                try: os.unlink(out_path)
                except: pass
                if task_id: sse_push(task_id, {"progress": 100, "audio": data, "mime": "audio/mpeg", "ok": True}); sse_done(task_id)
            if task_id:
                threading.Thread(target=run_tts, daemon=True).start()
                return send_json(h, {"ok": True, "async": True})
            subprocess.run([sys.executable, "-m", "edge_tts", "--voice", voice, "--rate", rate, "--text", text, "--write-media", out_path], capture_output=True, text=True, timeout=60)
            with open(out_path, "rb") as f: data = base64.b64encode(f.read()).decode()
            return send_json(h, {"audio": data, "mime": "audio/mpeg"})
        except Exception as e: return send_json(h, {"error": str(e)}, 500)
        finally:
            if out_path and os.path.exists(out_path):
                try: os.unlink(out_path)
                except: pass

    if p == "/sqlite_query":
        try:
            dbp = safe_path(body["path"]); sql = body.get("sql", "SELECT 1").strip()
            if any(sql.upper().startswith(d) for d in ("DROP TABLE", "DROP DATABASE", "TRUNCATE", "DELETE FROM sqlite_master")): return send_json(h, {"error": "Xavfli SQL buyrug'i bloklandi"}, 403)
            conn = sqlite3.connect(dbp); conn.row_factory = sqlite3.Row
            cur = conn.execute(sql); rows = [dict(r) for r in cur.fetchmany(500)]
            cols = list(rows[0].keys()) if rows else []; conn.close()
            return send_json(h, {"cols": cols, "rows": rows, "count": len(rows)})
        except Exception as e: return send_json(h, {"error": str(e)}, 500)

    if p == "/snippets_load":
        try:
            sfile = Path(HOME) / ".universal_analyzer_snippets.json"
            if sfile.exists(): return send_json(h, json.loads(sfile.read_text(encoding="utf-8")))
            return send_json(h, {"snippets": []})
        except Exception as e: return send_json(h, {"error": str(e)}, 500)

    return False
