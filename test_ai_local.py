import asyncio
import os
import sys
import io
from dotenv import load_dotenv

# Terminalni UTF-8 rejimiga o'tkazamiz
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Loyiha papkasini pathga qo'shamiz
sys.path.append(os.getcwd())

from utils.ai_engine import AIEngine

async def test_ai():
    load_dotenv()
    api_key = os.getenv('GEMINI_API_KEY')
    
    if not api_key:
        print("ERROR: .env ichida GEMINI_API_KEY topilmadi!")
        return

    print(f"AI Test boshlandi... Kalit: {api_key[:10]}***")
    
    try:
        # AIEngine ni yaratamiz
        engine = AIEngine([api_key])
        print(f"Ishlatilayotgan model: {engine.model_name}")
        
        print("Gemini'ga so'rov yuborilmoqda...")
        response = await engine.get_analysis("Salom, kodingni test qilyapman. Ishlayotgan bo'lsang 'OK' deb javob ber.", context_type="chat")
        
        print("\n--- AI JAVOBI ---")
        # Unicode xatolarini oldini olish uchun 'ignore' bilan chiqaramiz
        print(response.encode('utf-8', 'ignore').decode('utf-8'))
        print("-----------------\n")
        
        if "DRAFT" in response or "band" in response:
            print("WARNING: Bot 'Draft' rejimida javob berdi. API yoki Modelda muammo bor.")
        else:
            print("SUCCESS: AI to'g'ri ishlamoqda!")
            
    except Exception as e:
        print(f"XATOLIK YUZ BERDI: {e}")

if __name__ == "__main__":
    asyncio.run(test_ai())
