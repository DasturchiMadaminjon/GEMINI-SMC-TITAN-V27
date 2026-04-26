import asyncio
import google.generativeai as genai

async def check_new_key():
    key = "YOUR_KEY_HERE"
    print(f"Checking key: {key[:10]}...")
    try:
        genai.configure(api_key=key, transport='rest')
        models = genai.list_models()
        print("Available models for this key:")
        for m in models:
            if 'generateContent' in m.supported_generation_methods:
                print(f" - {m.name}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(check_new_key())

