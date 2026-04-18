import subprocess, os, io, re
from pathlib import Path
from handlers.utils import log, send_json, safe_path, unquote, cors, mimetypes

def handle_media(h, p, body):
    if p == "/ffmpeg":
        try:
            src = body.get("src", "")
            fmt = body.get("format", "mp3")
            try: src = safe_path(src)
            except (PermissionError, ValueError) as e: return send_json(h, {"error": str(e)}, 403)
            if not Path(src).is_file(): return send_json(h, {"error": "Fayl topilmadi"}, 404)
            ALLOWED_FMTS = {"mp3", "mp4", "wav", "ogg", "webm", "gif", "avi", "mkv", "flac", "aac", "m4a", "jpg", "png", "webp"}
            fmt = fmt.lower().strip()
            if fmt not in ALLOWED_FMTS: return send_json(h, {"error": f"Ruxsat etilmagan format: {fmt}"}, 400)
            out = str(Path(src).with_suffix("." + fmt))
            SAFE_FLAGS = {"-vn", "-an", "-vf", "-af", "-b:a", "-b:v", "-r", "-s", "-t", "-ss", "-to", "-acodec", "-vcodec", "-crf", "-preset", "-tune", "-movflags", "-ar", "-ac", "-map", "0:a", "0:v", "-q:a", "-q:v"}
            raw_extra = body.get("extra", [])
            if isinstance(raw_extra, str): raw_extra = raw_extra.split()
            safe_extra = []
            i = 0
            while i < len(raw_extra):
                flag = str(raw_extra[i])
                if flag in SAFE_FLAGS:
                    safe_extra.append(flag)
                    if i + 1 < len(raw_extra):
                        val = str(raw_extra[i + 1])
                        if not val.startswith("-") or val in SAFE_FLAGS:
                            safe_extra.append(val); i += 1
                i += 1
            result = subprocess.run(["ffmpeg", "-y", "-i", src] + safe_extra + [out], capture_output=True, text=True, timeout=120)
            if result.returncode != 0: return send_json(h, {"error": result.stderr[-500:]})
            return send_json(h, {"ok": True, "out": out})
        except FileNotFoundError: return send_json(h, {"error": "ffmpeg topilmadi"})
        except Exception as e:
            log.error("FFMPEG error: %s", e, exc_info=True); return send_json(h, {"error": str(e)}, 500)

    if p == "/pdf_annotate":
        try:
            from fpdf import FPDF
            from pypdf import PdfReader, PdfWriter
            fp = body.get("path", ""); notes = body.get("notes", [])
            reader = PdfReader(fp)
            overlay = FPDF(); overlay.set_auto_page_break(False)
            for note in notes:
                overlay.add_page()
                overlay.set_font("Helvetica", "", int(note.get("size", 12)))
                overlay.set_text_color(*[int(x) for x in note.get("color", "255,0,0").split(",")])
                overlay.set_xy(note.get("x", 10), note.get("y", 10))
                overlay.cell(0, 0, note.get("text", ""))
            buf = io.BytesIO(); overlay.output(buf); buf.seek(0)
            ol_reader = PdfReader(buf); writer = PdfWriter()
            for i, page in enumerate(reader.pages):
                if i < len(ol_reader.pages): page.merge_page(ol_reader.pages[i])
                writer.add_page(page)
            out = fp.replace(".pdf", "_annotated.pdf")
            with open(out, "wb") as f: writer.write(f)
            return send_json(h, {"ok": True, "out": out})
        except Exception as e: return send_json(h, {"error": str(e)}, 500)

    return False
def handle_media_get(h, p, qs):
    if p == "/media":
        try:
            fp_raw = qs.get("path", [""])[0]
            if not fp_raw: return send_json(h, {"error": "Path kerak"}, 400)
            fp = os.path.normpath(unquote(fp_raw))
            try: fp = safe_path(fp)
            except ValueError as e: return send_json(h, {"error": str(e)}, 403)
            f = Path(fp)
            if not f.is_file(): return send_json(h, {"error": "Fayl yo'q"}, 404)
            mime, _ = mimetypes.guess_type(str(f))
            size = f.stat().st_size
            range_hdr = h.headers.get("Range", "")
            if range_hdr:
                m = re.match(r"bytes=(\d+)-(\d*)", range_hdr)
                start = int(m.group(1)) if m else 0
                end = int(m.group(2)) if m and m.group(2) else size - 1
                chunk = end - start + 1
                h.send_response(206)
                h.send_header("Content-Type", mime or "application/octet-stream")
                h.send_header("Content-Range", f"bytes {start}-{end}/{size}")
                h.send_header("Content-Length", str(chunk))
                h.send_header("Accept-Ranges", "bytes")
                cors(h); h.end_headers()
                with open(fp, "rb") as fh:
                    fh.seek(start); h.wfile.write(fh.read(chunk))
            else:
                h.send_response(200)
                h.send_header("Content-Type", mime or "application/octet-stream")
                h.send_header("Content-Length", str(size))
                h.send_header("Accept-Ranges", "bytes")
                cors(h); h.end_headers()
                with open(fp, "rb") as fh:
                    while True:
                        chunk = fh.read(1024*1024)
                        if not chunk: break
                        h.wfile.write(chunk)
            return True
        except Exception as e:
            log.error("MEDIA GET error", exc_info=True)
            return send_json(h, {"error": str(e)}, 500)
    return False
