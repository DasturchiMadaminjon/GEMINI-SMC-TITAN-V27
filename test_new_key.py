import asyncio
import google.generativeai as genai

async def quick_test():
    key = "YOUR_KEY_HERE"
    print(f"Testing key: {key[:10]}...")
    try:
        genai.configure(api_key=key, transport='rest')
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content("Ping")
        print(f"SUCCESS: {response.text}")
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    asyncio.run(quick_test())
