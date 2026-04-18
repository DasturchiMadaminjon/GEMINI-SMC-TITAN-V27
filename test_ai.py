import asyncio, aiohttp, json, os
from dotenv import load_dotenv


async def test_all_models():
    load_dotenv()
    key = os.getenv('GEMINI_API_KEY', 'AIzaSyBCQpYzTI0lB9jdka7uDkCACXFqLsdBelw')

    # Ro'yxatingizdan eng munosib 3 ta model
    test_models = ["gemini-flash-latest", "gemini-2.0-flash-lite", "gemini-2.5-flash"]

    print(f"🚀 Modellar kvotasini tekshirish boshlandi...")
    async with aiohttp.ClientSession() as sess:
        for model in test_models:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
            payload = {"contents": [{"parts": [{"text": "Salom, test so'rovi."}]}]}

            print(f"📡 {model} sinab ko'rilmoqda...")
            try:
                async with sess.post(url, json=payload, timeout=20) as r:
                    res = await r.json()
                    if r.status == 200:
                        text = res['candidates'][0]['content']['parts'][0]['text']
                        print(f"✅ {model} MUKSMMAL ISHLAYAPTI! Javob: {text}")
                        return  # Bitta ishlaydigan model topilsa kifoya
                    else:
                        print(f"❌ {model} xatosi ({r.status})")
            except Exception as e:
                print(f"🔥 {model} ulanish xatosi: {e}")

    print("\n⚠️ Hech qaysi model ishlamadi. Iltimos, AI Studio'da kvotangizni tekshiring.")


if __name__ == "__main__":
    asyncio.run(test_all_models())
