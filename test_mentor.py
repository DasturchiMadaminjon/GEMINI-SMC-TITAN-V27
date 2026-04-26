import asyncio
import os
import sys
sys.stdout.reconfigure(encoding='utf-8')
import yaml
from utils.ai_engine import AIEngine

# Proxy settings if needed
if "PYTHONANYWHERE_DOMAIN" in os.environ:
    os.environ["HTTP_PROXY"] = "http://proxy.server:3128"
    os.environ["HTTPS_PROXY"] = "http://proxy.server:3128"

async def test_mentor_module():
    print("⏳ Trener modulini test qilish boshlandi...\n")
    try:
        with open('config/settings.yaml', 'r') as f:
            cfg = yaml.safe_load(f)
            keys = cfg.get('gemini_ai', {}).get('api_keys', [])
        
        # Initialize AI Engine
        ai = AIEngine(keys)
        
        # Simulated User Query (Yangi video va havolalarni so'rash logikasini tekshirish uchun)
        user_query = "BOS (Break of Structure) qanday hosil bo'ladi? Iltimos buni yaxshiroq tushunishim uchun rasm hamda YouTube video darslik qidiruv havolasi(ssilka) bilan tushuntirib bering."
        
        # Test: Mentor QA Persona (mavzuli dars)
        print(f"👤 Foydalanuvchi Savoli: {user_query}")
        print("--------------------------------------------------")
        
        # Test engine endi RAGEngine.search() ga bog'langan (test quruq API uchun mo'ljallangan yengil holatda)
        response = await ai.get_analysis(user_query, context_type="mentor_lessons")
        print("\n🎓 AI TRENER JAVOBI (mentor_lessons + RAG + Video Links qatlami):")
        print(response)
        
    except Exception as e:
        print(f"❌ Xatolik yuz berdi: {e}")

if __name__ == "__main__":
    asyncio.run(test_mentor_module())
