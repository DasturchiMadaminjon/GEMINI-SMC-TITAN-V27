import logging
import asyncio
import os
import base64
import google.generativeai as genai
from datetime import datetime, timezone

# --- PROXY VA LOGGING ---
if "PYTHONANYWHERE_DOMAIN" in os.environ:
    os.environ["HTTP_PROXY"] = "http://proxy.server:3128"
    os.environ["HTTPS_PROXY"] = "http://proxy.server:3128"

logger = logging.getLogger(__name__)

class AIEngine:
    def __init__(self, api_keys, model_name="gemini-2.0-flash"):
        # API kalitlarini tozalash va tayyorlash
        if isinstance(api_keys, str):
            self.api_keys = [k.strip() for k in [api_keys] if k and len(k) > 20]
        else:
            self.api_keys = [k.strip() for k in (api_keys or []) if k and len(k) > 20]
        
        self.current_key_index = 0
        self.model_name = model_name
        
        # Google SDK-ni PythonAnywhere proxy bilan ishlashga majburlash
        if self.api_keys:
            genai.configure(
                api_key=self.api_keys[self.current_key_index],
                transport='rest'  # MUHIM: Proxy orqali faqat REST barqaror ishlaydi
            )
            self.model = genai.GenerativeModel(self.model_name)
        else:
            self.model = None

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
1. Foydalanuvchi RASM yuborganida — chartni ko'rib SMC tahlil qiling (OB, FVG, Liquidity)
2. Foydalanuvchi SAVOL berganda — sodda va ta'limiy tilda javob bering
3. Javob uzun bo'lmassin, aniq va foydali bo'lsin
4. Har doim O'zbek tilida yozing
5. Tahlil oxirida qisqa savdo tavsiyasi bering"""
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
            self.model = genai.GenerativeModel(self.model_name)
            logger.info(f"API key rotated → index {self.current_key_index}")
            return True
        return False

    async def get_analysis(self, prompt: str, context_type: str = "technical", image_bytes: bytes = None) -> str:
        """Kompaniya rasmiy metodologiyasi asosida AI analiz qilish"""
        if not self.model:
            return "❌ API kalitlari sozlanmagan."

        persona = self.personas.get(context_type, self.personas["technical"])

        now = datetime.now(timezone.utc)
        header = (
            f"[SANA: {now.strftime('%d.%m.%Y')} | VAQT UTC: {now.strftime('%H:%M')} | "
            f"UZT: {(now.hour+5)%24:02d}:{now.minute:02d}]\n"
            f"[ESLATMA: Faqat 2025-2026 voqealarini 'hozirgi' deb tan. O'zbek tilida javob ber.]\n\n"
        )

        full_prompt = f"{header}{persona}\n\nSO'ROV: {prompt}"

        contents = [full_prompt]
        if image_bytes:
            contents.append({
                "mime_type": "image/jpeg",
                "data": image_bytes
            })

        last_error = ""

        # Kalitlarni aylanib chiqish (limitlarga tushmasligi uchun)
        for _ in range(len(self.api_keys)):
            try:
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: self.model.generate_content(contents)
                )
                if response and response.text:
                    logger.info(f"AI ✅ [{self.model_name}] → {context_type.upper()}")
                    return response.text
            except Exception as e:
                last_error = str(e)
                # Limit tugagan yoki ruxsat etilmagan xatoliklar
                if "429" in last_error or "403" in last_error:
                    if self._rotate_key():
                        continue
                break

        # Barcha kalitlar tugaganda Draft Mode
        if "429" in last_error or "404" in last_error or "503" in last_error:
            logger.error(f"FINAL AI XATOSI: {last_error}")
            return self.drafts.get(context_type, self.drafts["technical"])

        logger.error(f"KUTILMAGAN AI XATOSI: {last_error}")
        return f"❌ Xatolik: {last_error[:200]}"

    async def analyze_text(self, text, persona_type="technical"):
        """Tahlil qilish uchun asosiy funksiya (Oson ishlatish uchun wrapper)"""
        try:
            return await self.get_analysis(prompt=text, context_type=persona_type)
        except Exception as e:
            logger.error(f"AI Engine xatosi: {e}")
            return "Kechirasiz, tahlil qilishda xatolik yuz berdi."
