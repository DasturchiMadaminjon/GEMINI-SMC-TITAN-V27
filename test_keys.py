import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
api_keys = [k.strip() for k in os.getenv('GEMINI_API_KEY', '').split(',') if len(k.strip()) > 20]

print(f"Testing {len(api_keys)} keys (Quick Test)...")

for i, key in enumerate(api_keys):
    print(f"Key #{i+1} [{key[:8]}...]: ", end="")
    try:
        genai.configure(api_key=key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        # timeout bo'lmasligi uchun juda kichik so'rov
        response = model.generate_content("Ping")
        print(f"[OK] WORKS! ({response.text.strip()[:10]})")
    except Exception as e:
        print(f"[ERROR] FAILED: {str(e)[:50]}")
print("Done.")
