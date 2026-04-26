import asyncio
import os
import sys
import io
import google.generativeai as genai
from dotenv import load_dotenv

if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

async def test_all_keys():
    load_dotenv()
    raw_keys = os.getenv('GEMINI_API_KEY')
    
    if not raw_keys:
        print("ERROR: GEMINI_API_KEY topilmadi!")
        return

    keys = [k.strip() for k in raw_keys.split(',') if k.strip()]
    print(f"Jami {len(keys)} ta kalit topildi. Tekshirilmoqda...\n")

    for i, key in enumerate(keys):
        print(f"--- Kalit #{i+1}: {key[:10]}... ---")
        try:
            genai.configure(api_key=key, transport='rest')
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            # Oddiy so'rov
            response = model.generate_content("Ping")
            if response and response.text:
                print(f"✅ ISHLAYAPTI! Javob: {response.text[:20]}")
            else:
                print("⚠️ Javob bo'sh qaytdi.")
        except Exception as e:
            err = str(e)
            if "API_KEY_INVALID" in err:
                print("❌ XATOLIK: Kalit noto'g'ri (Invalid)")
            elif "429" in err:
                print("❌ XATOLIK: Limit tugagan (Rate Limit)")
            else:
                print(f"❌ XATOLIK: {err[:100]}")
        print("-" * 30)

if __name__ == "__main__":
    asyncio.run(test_all_keys())
