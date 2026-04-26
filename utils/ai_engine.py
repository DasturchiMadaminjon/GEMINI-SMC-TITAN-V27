import logging
import asyncio
import os
import sys
import base64

# PythonAnywhere uchun .local kutubxonalarini yo'lga qo'shish
local_path = os.path.expanduser("~/.local/lib/python3.13/site-packages")
if local_path not in sys.path:
    sys.path.append(local_path)

import google.generativeai as genai
from datetime import datetime, timezone
from utils.price_fetcher import get_current_price

# --- PROXY VA LOGGING ---
if "PYTHONANYWHERE_DOMAIN" in os.environ:
    os.environ["HTTP_PROXY"] = "http://proxy.server:3128"
    os.environ["HTTPS_PROXY"] = "http://proxy.server:3128"

logger = logging.getLogger(__name__)

class AIEngine:
    def __init__(self, api_keys, model_name="gemini-flash-latest"):
        # API kalitlarini tozalash va tayyorlash
        if isinstance(api_keys, str):
            # Vergul bilan ajratilgan bo'lsa, ro'yxatga aylantiramiz
            self.api_keys = [k.strip() for k in api_keys.split(',') if k.strip() and len(k.strip()) > 20]
        else:
            self.api_keys = [k.strip() for k in (api_keys or []) if k and len(k) > 20]
        
        self.current_key_index = 0
        self.model_name = model_name
        
        # Google SDK-ni PythonAnywhere proxy bilan ishlashga majburlash
        if self.api_keys:
            genai.configure(
                api_key=self.api_keys[self.current_key_index],
                transport='rest'
            )
            # AVTO-ANIQLASH: Ishlaydigan modelni o'zi topsin
            try:
                available = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                if available:
                    # 'gemini-1.5-flash' yoki shunga o'xshashini qidirish, bo'lmasa birinchisi
                    best_match = next((m for m in available if "flash" in m), available[0])
                    self.model_name = best_match.replace("models/", "")
                    print(f"[AI AUTO] Ishchi model aniqlandi: {self.model_name}")
                else:
                    raise Exception("Hech qanday model topilmadi")
            except Exception as e:
                print(f"[AI MODELS] Avto-aniqlash xatosi: {e}")
                
            # Tool-larni ro'yxatga olish
            tools = [get_current_price]
            self.model = genai.GenerativeModel(
                model_name=self.model_name,
                tools=tools
            )
        else:
            self.model = None

        # RAG Engine ni avto yuklash
        try:
            from utils.rag_engine import RAGEngine
            self.rag = RAGEngine(self.api_keys)
        except Exception as e:
            logger.error(f"Failed to initialize RAG: {e}")
            self.rag = None

        # =====================================================
        # PERSONA TIZIMI
        # =====================================================
        self.personas = {
            "technical": """Siz "SMC TITAN" ekspertisiz. Quyidagi aniq formatda javob bering:

**BOZOR STRUKTURASI:**
- Trend: [Bullish/Bearish/Sideways] (HTF)
- BOS/CHoCH: [Tasvirlab bering]

**ASOSIY ZONALAR:**
- 🟢 Talab (Demand OB): [Narx diapazoni]
- 🔴 Taklif (Supply OB): [Narx diapazoni]
- FVG: [Mavjud bo'lsa ko'rsating]

**LIKVIDLIK:**
- SSL (Pastki maqsad): [Daraja]
- BSL (Yuqori maqsad): [Daraja]

**SAVDO REJASI:**
- Kirish: [Daraja va shart]
- Stop-Loss: [Daraja]
- TP1 / TP2 / TP3: [Darajalar]
- Sifat Ball: [X/100]""",

            "scalping": """Siz "SCALP MASTER"siz. FAQAT M5/M15 taymfreymlar uchun quyidagi formatda javob bering:

**M15 HOLAT:**
- Tezkor trend: [Yo'nalish]
- Eng yaqin OB: [Zona]

**KIRISH REJASI:**
- 🎯 Long kirish: [Narx] | SL: [Narx] | TP: [Narx]
- 🎯 Short kirish: [Narx] | SL: [Narx] | TP: [Narx]

**LIKVIDLIK SWEEP:**
- Keyingi maqsad: [Daraja]
- [Rasm yuborilgan bo'lsa, undagi chartni tahlil qiling]

**XAVF:** [Kam/O'rtacha/Yuqori] | R:R: [1:X]""",

            "fundamental": """Siz "MACRO ANALYST"siz. FAQAT fundamental omillar haqida yozing, SMC yoki grafik chiziqlarini AYTMANG:

**MAKRO HOLAT:**
- DXY (Dollar indeksi): [Kuchli/Zaif + sabab]
- FED/CB Siyosat: [Hozirgi pozitsiya, keyingi kutilma]

**ASOSIY DRAYVERLAR:**
- 📰 Eng muhim yangilik: [Tavsiflang]
- 📊 Kelgusi muhim ma'lumot: [NFP/CPI/va h.k.]
- 🌍 Geosiyosat: [Ta'siri]

**SENTIMENT:**
- Risk-On / Risk-Off: [Qaysi biri va nima uchun]
- Institusional pozitsiya: [Tahlil]

**XULOSA:** [3-4 jumlada aniq yakuniy fikr]""",

            "chat": """Siz "SMC MENTOR"siz. Qoidalar:
1. Foydalanuvchi RASM yuborganida — chart tahlil qiling (OB, FVG, Liquidity).
ENG MUHIMI: Rasmda indikator paneli bo'lsa, undagi matnlarga (masalan "SL Urildi", "Yopiq", "TP Urildi") alohida e'tibor qarating. Agar "SL Urildi" yozuvi bo'lsa yoki grafikdagi pozitsiya (qizil quti) urilib bo'lgan bo'lsa: "Bu trade allaqachon SL bilan yopilgan, bozor Inducement (aldamchi harakat) qildi. Keyingi signalni kuting" deb izoh bering.
2. SAVOL berganda — sodda va ta'limiy tilda javob bering.
3. Javob uzun bo'lmassin, aniq va foydali bo'lsin.
4. Har doim O'zbek tilida yozing.
5. Sizda real vaqt rejimida NARXLARNI olish imkoniyati bor (XAUUSD, BTCUSD va hk). Agar foydalanuvchi narx so'rasa, `get_current_price` funksiyasidan foydalaning.""",

            "analytics": """Siz yuqori malakali "Hedge Fund Menejeri"siz. Sizga robotning oxirgi 50 ta bitimi (signallari) statistikasi beriladi.
Qoidalaringiz:
1. Qaysi instrument ko'p foyda yoki zarar keltirganini baholang.
2. Nega bunday bo'lganligini ehtimoliy sababini ayting.
3. Men strategiyani qanday o'zgartirish kerakligi haqida amaliy va professional tavsiya bering.
4. Javobingiz aniq, statistik va 3 ta abzasdan iborat bo'lsin.""",

            "mentor_lessons": """SMC metodikasi asoslarini o'rgatuvchi qattiqqo'l va professional Ustoze (Mentor) roliga kir.
Faqat Smart Money Concepts (SMC) doirasidagi mavzularni tushuntir (Liquidity, Order Flow, BOS, CHoCH, FVG, Inducement).
Agar o'quvchida rasm (grafik vizualizatsiya) yoki chuqurroq ko'rish ehtiyoji bo'lsa, mavzuni ko'rsatib ishonchli YouTube video darsliklar yoki rasm havolalarini (ssilka) xabar ichida doim markdown formatda yubor: masalan [Mavzu bo'yicha YouTube darsligi](https://www.youtube.com/results?search_query=smart+money+concepts+BOS).
Chakana (Retail) analizni rad et. Har bir o'rgatgan darsingga kichik uy vazifasi berib ket.""",

            "mentor_live_examples": """Siz SMC TRENERisiz. Vazifangiz: Foydalanuvchi so'ragan terminni yoki so'rovni HOZIRGI JONLI GLOBAL BOZOR (Masalan oxirgi NFP yangiligi bilan yoki XAUUSD/BTCdagi oxirgi sweep bilan) bog'lab tushuntirib berish. Eski vizual tarixni emas, imkon boricha hozirgi yoki yaqin kungi makro-holatni tilga oling.""",

            "mentor_qa": """Siz SMC GIBRID MENTOR CHATbotisiz. Foydalanuvchi erkin savol beradi. Retail trading savollarini aqlli va piching bilan (lekin xushmuomala) rad eting, haqiqiy SMC (Liquidity, BOS, CHoCH) bo'lsa darxol tushuntiring. Javoblarda o'quvchini ilhomlantiring.
MUHIM ISTISNO: Agar foydalanuvchi O'zbekiston qonunchiligi, Soliq siyosati, Legal ro'yxatdan o'tgan brokerlar yoki halollik kabi jiddiy huquqiy/hayotiy masalalarda savol so'rasa, piching qilmang. Bu mavzuning jiddiyligini inobatga olib ochiq do'stona, aniq yuridik tavsiya bering (masalan: daromaddan soliq to'lash majburiyati yoki lisenzitsiyalangan vositachilar ҳақида).
O'quvchi savol yoki chart (rasm) tashlasa, xato va kamchiliklarini qattiq tahlil qilib ko'rsat.
Agar o'quvchi xato o'ylayotgan bo'lsa uni koyib, To'g'ri chizilgan SMC strukturasini ko'rish uchun xorijiy trading saytlardagi rasm havolalariga (ssilkalarga) yoki YouTube video qidiruv natijalariga yo'naltir: [To'g'ri SMC modeli](https://www.youtube.com/results?search_query=smc+order+block+trading).
SMC terminlarini qo'llagin. Rasm ulanilgan bo'lsa (vision) vizual likvidlikni belgilab ber."""
        }

        # Draft Mode — API limit tugaganda (barqaror zaxira)
        self.drafts = {
            "technical": "⚠️ <b>DRAFT MODE:</b> BOS/CHoCH kuzating. Fibo 0.618-0.786 'Discount' zonasiga kiring. Order Block tasdig'ini kuting.",
            "scalping":  "⚠️ <b>SCALP DRAFT:</b> M5 likvidlik sweep va CHoCH ni kuting. Shoshilmang.",
            "fundamental":"⚠️ <b>MACRO DRAFT:</b> DXY va FED ritorikasini kuzating. NFP/CPI kalendarni tekshiring.",
            "chat":      "⚠️ <b>MENTOR DRAFT:</b> AI band. SMC asosi: Struktura → Likvidlik → Kirish."
        }

    def _rotate_key(self):
        if len(self.api_keys) > 1:
            self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
            genai.configure(
                api_key=self.api_keys[self.current_key_index],
                transport='rest'
            )
            # Model nomini tozalab yangitdan yaratish
            clean_name = self.model_name.replace("models/", "")
            self.model = genai.GenerativeModel(clean_name)
            logger.info(f"API key rotated → index {self.current_key_index} (Model: {clean_name})")
            return True
        return False

    async def get_analysis(self, prompt: str, context_type: str = "technical", image_bytes: bytes = None) -> str:
        """Kompaniya rasmiy metodologiyasi asosida AI analiz qilish"""
        if not self.model:
            return "❌ API kalitlari sozlanmagan yoki noto'g'ri."

        persona = self.personas.get(context_type, self.personas["technical"])

        now = datetime.now(timezone.utc)
        header = (
            f"[SANA: {now.strftime('%d.%m.%Y')} | VAQT UTC: {now.strftime('%H:%M')} | "
            f"UZT: {(now.hour+5)%24:02d}:{now.minute:02d}]\n"
            f"[ESLATMA: Faqat 2025-2026 voqealarini 'hozirgi' deb tan. O'zbek tilida javob ber.]\n\n"
        )

        # RAG (Vector Database) qidiruvi
        rag_text = ""
        if context_type in ["mentor_lessons", "mentor_qa"] and getattr(self, 'rag', None):
            rag_text = self.rag.search(prompt)

        full_prompt = f"{header}{persona}\n\n"
        if rag_text:
            full_prompt += f"--- MAXFIY BILIM BAZASI (RAG_MATN) ---\n{rag_text}\n--------------------------\n\n"
        full_prompt += f"SO'ROV: {prompt}"

        contents = [full_prompt]
        if image_bytes:
            contents.append({
                "mime_type": "image/jpeg",
                "data": image_bytes
            })

        last_error = ""

        # Kalitlarni aylanib chiqish (limitlarga yoki bloklarga tushmasligi uchun)
        for attempt in range(len(self.api_keys)):
            try:
                loop = asyncio.get_event_loop()
                # Chat obyektidan foydalanamiz (Auto Function Calling uchun)
                chat = self.model.start_chat(enable_automatic_function_calling=True)
                response = await loop.run_in_executor(
                    None,
                    lambda: chat.send_message(contents)
                )
                if response and response.text:
                    logger.info(f"AI OK [{self.model_name}] attempt={attempt}")
                    return response.text
            except Exception as e:
                last_error = str(e)
                # 400 (expired), 403 (leaked/invalid), 429 (rate limit), 503 (server)
                is_key_error = any(x in last_error for x in [
                    "400", "403", "429", "503", "API_KEY_INVALID", "expired", "leaked"
                ])
                if is_key_error and self._rotate_key():
                    logger.warning(f"Key rotated (attempt {attempt+1}): {last_error[:60]}")
                    continue
                # Boshqa xatolikda ham keyingi kalitni sinab ko'ramiz
                logger.warning(f"AI xatolik (attempt {attempt+1}): {last_error[:80]}")
                self._rotate_key()

        # Barcha kalitlar tugagandan keyin xato turi bo'yicha javob
        if "429" in last_error:
            return self.drafts.get(context_type, self.drafts["technical"])
        if any(x in last_error for x in ["403", "leaked"]):
            return "❌ XATO: API kalitlaringiz bloklangan (Leaked). Yangi kalit oling."
        if any(x in last_error for x in ["400", "expired", "API_KEY_INVALID"]):
            return "❌ XATO: API kalitlar muddati tugagan. .env faylini yangilang."

        logger.error(f"FINAL AI XATOSI: {last_error}")
        return f"❌ AI xatoligi: {last_error[:100]}"

    async def analyze_text(self, text, persona_type="technical"):
        """Tahlil qilish uchun asosiy funksiya (Oson ishlatish uchun wrapper)"""
        try:
            return await self.get_analysis(prompt=text, context_type=persona_type)
        except Exception as e:
            logger.error(f"AI Engine xatosi: {e}")
            return f"❌ Xatolik: {str(e)[:100]}"
