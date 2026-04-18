import json, urllib.request
from handlers.utils import rate_limit, log, send_json, HAS_GENAI

def handle_ai(h, p, body):
    # ── Claude API ────────────────────────────────────────────────────
    if p == "/claude":
        if not rate_limit("claude", 20, 60): 
            return send_json(h, {"error": "Rate limit: 20 so'rov/daqiqa"}, 429)
        try:
            key = body.pop("api_key", "")
            hdr = {"Content-Type": "application/json", "anthropic-version": "2023-06-01"}
            if key: hdr["x-api-key"] = key
            req = urllib.request.Request("https://api.anthropic.com/v1/messages",
                                         data=json.dumps(body).encode(), headers=hdr, method="POST")
            with urllib.request.urlopen(req, timeout=120) as r:
                return send_json(h, json.loads(r.read()))
        except urllib.error.HTTPError as e:
            return send_json(h, json.loads(e.read()), e.code)
        except Exception as e:
            log.error("claude error", exc_info=True)
            return send_json(h, {"error": str(e)}, 500)

    # ── Gemini API ────────────────────────────────────────────────────
    if p == "/gemini":
        if not HAS_GENAI: return send_json(h, {"error": "pip install google-generativeai"}, 500)
        try:
            import google.generativeai as genai
            key = body.get("api_key", "")
            if key: genai.configure(api_key=key)
            model = genai.GenerativeModel(body.get("model", "gemini-2.0-flash"),
                                          system_instruction=body.get("system") or None)
            msgs = body.get("messages", [])
            hist = [{"role": "user" if m["role"] == "user" else "model", "parts": [m["content"]]} for m in msgs[:-1]]
            chat = model.start_chat(history=hist)
            resp = chat.send_message(msgs[-1]["content"] if msgs else "")
            return send_json(h, {"text": resp.text})
        except Exception as e:
            log.error("gemini error", exc_info=True)
            return send_json(h, {"error": str(e)}, 500)

    if p == "/gemini_upload":
        if not HAS_GENAI: return send_json(h, {"error": "pip install google-generativeai"}, 500)
        try:
            import google.generativeai as genai
            key = body.get("api_key", "")
            if key: genai.configure(api_key=key)
            up = genai.upload_file(path=body["path"])
            return send_json(h, {"uri": up.uri, "mimeType": up.mime_type, "name": up.name})
        except Exception as e:
            log.error("gemini_upload error", exc_info=True)
            return send_json(h, {"error": str(e)}, 500)

    if p == "/gemini_analyze":
        if not HAS_GENAI: return send_json(h, {"error": "pip install google-generativeai"}, 500)
        try:
            import google.generativeai as genai
            key = body.get("api_key", "")
            if key: genai.configure(api_key=key)
            model = genai.GenerativeModel("gemini-2.0-flash")
            file_ref = genai.get_file(body["name"])
            resp = model.generate_content([file_ref, body.get("prompt", "Tahlil qil")])
            return send_json(h, {"text": resp.text})
        except Exception as e:
            log.error("gemini_analyze error", exc_info=True)
            return send_json(h, {"error": str(e)}, 500)

    if p == "/gemini_models":
        if not HAS_GENAI: return send_json(h, {"error": "pip install google-generativeai"}, 500)
        try:
            import google.generativeai as genai
            key = body.get("api_key", "")
            if key: genai.configure(api_key=key)
            models = []
            for m in genai.list_models():
                models.append({"name": m.name, "display_name": m.display_name,
                               "supported_methods": m.supported_generation_methods})
            return send_json(h, {"models": models, "count": len(models)})
        except Exception as e:
            return send_json(h, {"error": str(e)}, 500)

    return False # Not handled
