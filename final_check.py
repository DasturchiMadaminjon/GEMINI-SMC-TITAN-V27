import asyncio
import google.generativeai as genai

async def final_test():
    key = "YOUR_KEY_HERE"
    try:
        genai.configure(api_key=key, transport='rest')
        # Eng barqaror "latest" aliasidan foydalanamiz
        model = genai.GenerativeModel('gemini-flash-latest')
        response = model.generate_content("Ping")
        if response and response.text:
            print(f"SUCCESS: {response.text}")
        else:
            print("Empty response")
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    asyncio.run(final_test())

