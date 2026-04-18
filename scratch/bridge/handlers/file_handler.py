import os, shutil, base64, mimetypes, zipfile
from pathlib import Path
from handlers.utils import log, send_json, safe_path, HOME, unquote

def handle_file_get(h, p, qs):
    fp = os.path.normpath(unquote(qs.get("path", [HOME])[0]))

    if p == "/list":
        try:
            try:
                fp = safe_path(fp)
            except (PermissionError, ValueError) as e:
                return send_json(h, {"error": str(e)}, 403 if isinstance(e, PermissionError) else 400)
            d = Path(fp)
            if not d.exists(): return send_json(h, {"error": "Topilmadi"}, 404)
            if d.is_file(): return send_json(h, {"error": "Bu fayl"}, 400)
            it_list = list(d.iterdir())
            total = len(it_list)
            it_list.sort(key=lambda x: (x.is_file(), x.name.lower()))
            items = []
            limit = int(qs.get("limit", [1000])[0])
            for it in it_list[:limit]:
                try:
                    st = it.stat()
                    items.append({"name": it.name, "path": str(it),
                                  "type": "file" if it.is_file() else "folder",
                                  "size": st.st_size if it.is_file() else None,
                                  "ext": it.suffix.lower() if it.is_file() else None})
                except:
                    pass
            par = str(d.parent) if str(d) != str(d.parent) else None
            return send_json(h, {"path": str(d), "parent": par, "items": items, "total": total, "truncated": total > limit})
        except Exception as e:
            return send_json(h, {"error": str(e)}, 500)

    if p == "/read":
        try:
            try:
                fp = safe_path(fp)
            except (PermissionError, ValueError) as e:
                return send_json(h, {"error": str(e)}, 403 if isinstance(e, PermissionError) else 400)
            f = Path(fp)
            if not f.is_file(): return send_json(h, {"error": "Fayl yo'q"}, 404)
            size = f.stat().st_size
            if size > 15 * 1024 * 1024: 
                return send_json(h, {"error": f"Juda katta ({size // 1024}KB). Max 15MB."}, 400)
            mime, _ = mimetypes.guess_type(str(f))
            raw = f.read_bytes()
            if mime and mime.startswith("image/"):
                return send_json(h, {"type": "image", "mime": mime, "data": base64.b64encode(raw).decode(), "name": f.name})
            for enc in ("utf-8", "cp1251", "cp1252", "latin-1"):
                try:
                    txt = raw.decode(enc)
                    return send_json(h, {"type": "text", "content": txt, "name": f.name, "size": size, "enc": enc})
                except:
                    pass
            hex_prev = " ".join(f"{b:02x}" for b in raw[:512])
            return send_json(h, {"type": "binary", "mime": mime or "application/octet-stream",
                                   "hex": hex_prev, "data": base64.b64encode(raw).decode(), "name": f.name,
                                   "size": size})
        except Exception as e:
            return send_json(h, {"error": str(e)}, 500)

    return False

def handle_file_post(h, p, body):
    if p == "/write":
        try:
            wp = safe_path(body["path"])
            f = Path(wp)
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(body["content"], encoding=body.get("enc", "utf-8"))
            log.info("WRITE %s", wp)
            return send_json(h, {"ok": True})
        except Exception as e:
            log.error("WRITE error", exc_info=True)
            return send_json(h, {"error": str(e)}, 500)

    if p == "/mkdir":
        try:
            mp = safe_path(body["path"])
            Path(mp).mkdir(parents=True, exist_ok=True)
            return send_json(h, {"ok": True})
        except Exception as e:
            log.error("mkdir error", exc_info=True)
            return send_json(h, {"error": str(e)}, 500)

    if p == "/rename":
        try:
            src = safe_path(body["src"])
            dst = safe_path(body["dst"])
            Path(src).rename(dst)
            log.info("RENAME %s -> %s", src, dst)
            return send_json(h, {"ok": True})
        except Exception as e:
            log.error("RENAME error", exc_info=True)
            return send_json(h, {"error": str(e)}, 500)

    if p == "/delete":
        try:
            dp = safe_path(body["path"])
            f = Path(dp)
            shutil.rmtree(f) if f.is_dir() else f.unlink()
            log.info("DELETE %s", dp)
            return send_json(h, {"ok": True})
        except Exception as e:
            log.error("DELETE error", exc_info=True)
            return send_json(h, {"error": str(e)}, 500)

    if p == "/copy":
        try:
            src = safe_path(body["src"])
            dst = safe_path(body["dst"])
            s, d = Path(src), Path(dst)
            shutil.copy2(s, d) if s.is_file() else shutil.copytree(s, d)
            log.info("COPY %s -> %s", src, dst)
            return send_json(h, {"ok": True})
        except Exception as e:
            log.error("COPY error", exc_info=True)
            return send_json(h, {"error": str(e)}, 500)

    if p == "/zip_create":
        try:
            out = safe_path(body["out"])
            with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
                for fp in body["paths"]:
                    try: sfp = safe_path(fp)
                    except: continue
                    f = Path(sfp)
                    z.write(sfp, f.name)
            return send_json(h, {"ok": True, "out": out})
        except Exception as e:
            log.error("zip_create error", exc_info=True)
            return send_json(h, {"error": str(e)}, 500)

    return False
