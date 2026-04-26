import asyncio
import os
import sys
import google.generativeai as genai
from dotenv import load_dotenv

async def check_available_models():
    load_dotenv()
    raw_keys = os.getenv('GEMINI_API_KEY')
    keys = [k.strip() for k in raw_keys.split(',') if k.strip()]
    
    for key in keys:
        print(f"\n--- Checking key: {key[:10]}... ---")
        try:
            genai.configure(api_key=key, transport='rest')
            print("Available models:")
            models = genai.list_models()
            found = False
            for m in models:
                if 'generateContent' in m.supported_generation_methods:
                    print(f" - {m.name}")
                    found = True
            if not found:
                print("No content generation models found for this key.")
        except Exception as e:
            print(f"Error for this key: {e}")

if __name__ == "__main__":
    asyncio.run(check_available_models())
