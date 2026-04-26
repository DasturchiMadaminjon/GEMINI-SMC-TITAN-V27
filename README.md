# 🚀 GEMINI SMC TITAN V27 — Professional Terminal Suite (Fibo-Engulf Edition)

**Gemini SMC Titan V27** — dunyo bo'yicha eng kuchli SMC (Smart Money Concepts) logikasi asosida yaratilgan, Gemini AI va MT5/UzNEX bilan integratsiya qilingan savdo terminali.

---

## 🌟 V27 Titan — Yangi imkoniyatlar:
- ✅ **Fibo-Engulf Entry** — Engulfing shamini aniqlash va 0.5/0.618 Fibonachchi darajalariga avtomatik limit orderlar qo'yish.
- ✅ **2% Risk Split** — Jami 2% riskni ikkita 1% li kirish nuqtalariga (0.5 va 0.618) bo'lish orqali kirish narxini (fill) optimallashtirish.
- ✅ **Professional Feedback Loop** — Har bir Stop-Loss (SL) dan so'ng, bot avtomatik ravishda keyingi signal uchun sifat (minQuality) talabini oshiradi.
- ✅ **Direct Exchange Execution** — UzNEX va Binance birjalari bilan to'g'ridan-to'g'ri API orqali savdo qilish.
- ✅ **MTF Trend Guardian** — 15M signalini 1H ema200 trendi bilan tasdiqlash.
- ✅ **SQLite Database** — Barcha signallar va AI chat tarixi abadiy saqlanadi.
- ✅ **Multi-API Key Rotation** — Kalit limit tushganda avtomatik keyingi kalitga o'tish.
- ✅ **Real-time Price Tool** — AI orqali har qanday instrumentning joriy narxini bilish (Function Calling).

---

## 📂 Arxitektura Tuzilmasi:
```
gemini_bot/
├── bot.py                  ← Tizim boshqaruv markazi va Looplar
├── core/
│   ├── indicator.py        ← SMC Analiz O'zagi, Engulfing + Fibonacci mantiqi
│   ├── manager.py          ← Savdo boshqaruvi, Risk Splitting va Feedback Loop
│   └── watcher.py          ← MTF Trend kuzatuvchisi va kesh nazorati
├── utils/
│   ├── ai_engine.py        ← AI model integratsiyasi (Gemini)
│   ├── analytics.py        ← Savdo statistikasi va matnli hisobot
│   ├── chart_generator.py  ← Grafik generatsiya qilish mantiqi
│   ├── dashboard.py        ← Professional Web Terminal (Localhost:8080)
│   ├── database.py         ← SQLite Baza (Bitimlar va AI chat xotirasi)
│   ├── exchange.py         ← Yahoo/Binance/UzNEX Market Data va Order Client
│   ├── mt5_signal.py       ← MT5 Execution va Lot Calculation
│   ├── persistence.py      ← Bot holatini doimiy xotirada saqlash
│   ├── position_sizer.py   ← Optimal lot hajmini hisoblash
│   ├── rag_engine.py       ← RAG tizimi, PDF hujjatlardan bilim izlash
│   ├── sms.py              ← SMS yuborish mantiqi
│   ├── telegram.py         ← AI Chat va Remote Control (Signals)
│   ├── tradingview.py      ← TradingView dan ma'lumot olish
│   └── websocket_client.py ← Vebsoketlar orqali ulanish moduli
└── bilim_bazasi/            ← Strategiya qo'llanmalari (PDF va darsliklar)
```

---

## ⚡ Ishga tushirish (Setup Guide):
1. Kutubxonalarni yangilash: `pip install -r requirements.txt`
2. `.env` faylida API kalitlarini belgilang: `GEMINI_API_KEY=...`
3. Signal sifatini belgilang: `config/settings.yaml` → `smc.min_quality: 75.0`
4. Start: `python bot.py`

---

## 📈 Monitoring:
Bot ishga tushgach, brauzeringizda **`http://localhost:8080`** manziliga kiring (Password: `gemini2024`). U yerda barcha bitimlar, balans va AI javoblarini jonli ko'rasiz.

**Professional treyding terminalingiz muvaffaqiyatli ishga tushdi!** 🚀

---

## 📖 Professional Qo'llanma (Titan V27 Guide)

### 1. Dasturning Maqsadi
**Gemini SMC Titan V27** — bu professional treyderlar uchun mo'ljallangan avtomatlashtirilgan analitika tizimi. Uning asosiy vazifasi bozordagi "aqlli pul" (Smart Money) harakatlarini 24/7 rejimida matematik aniqlikda kuzatib borish va treyderni eng sifatli kirish zonalari bilan ta'minlashdir.

### 2. Panel Tugmalari va Vazifalari
*   **📊 Texnik Tahlil**: Joriy grafikdagi SMC strukturasini (BOS, CHoCH, OB) Gemini AI yordamida matnli izohlab beradi.
*   **🌐 Fundamental**: Bozorga ta'sir qiluvchi global iqtisodiy yangiliklarni tahlil qiladi.
*   **⚡ Scalping AI**: Kichik taymfreymlarda (1m, 5m) tezkor "Engulfing" setupslarini qidiradi.
*   **💬 AI Chat Assistant**: Bozor haqidagi har qanday savolingizga jonli ma'lumotlar asosida javob beradi.
*   **⚖️ Risk Status**: Hisob balansining xavfsizlik darajasini nazorat qiladi.
*   **🚨 PANIC CLOSE ALL**: Favqulodda vaziyatlarda barcha ochiq bitimlarni soniyalar ichida yopadi.

### 3. Real Hayotdagi Foydasi
*   **Vaqtni 10 barobar tejaydi**: Bot 5 ta instrumentni har daqiqada tahlil qiladi, bu esa inson uchun jismonan imkonsiz.
*   **Emotsional barqarorlik**: Kirish va chiqish qarorlari faqat qidirilgan qoidalar (Rules) asosida qabul qilinadi.
*   **Signal Sifati (minQuality)**: Har bir signal 0 dan 100 gacha ball bilan baholanadi. Bot faqat 75 balldan yuqori signallarni yetkazadi.

### 4. Sun'iy Intellekt (Gemini AI) va Bilim Bazasi
Dastur **Google Gemini 1.5 Flash** modeliga integratsiya qilingan (auto-detect orqali eng tez ishlaydigan model tanlanadi).
*   **AI foydasi**: Faqat grafikdagi chiziqlarni emas, balki "market sentiment"ni tushunadi.
*   **Bilim Bazasi**: Botning algoritmi ichiga professional SMC darsliklari va Fibo-Engulfing qoidalari kodlangan.

---

## ⚙️ Signal Sifatini Sozlash

`config/settings.yaml` faylini oching:

```yaml
smc:
  min_quality: 75.0   # ✅ STANDART (tavsiya etilgan) — faqat A+ signallar
  # min_quality: 65.0 # ⚠️ KO'PROQ signal olish uchun (past filtr)
  # min_quality: 80.0 # 🔒 FAQAT ENG YAXSHI signallar (kam, lekin ishonchli)
```

| Qiymat | Signal soni | Tavsiya |
|---|---|---|
| `65.0` | Ko'p (kun 10-15 ta) | Test va o'rganish uchun |
| `75.0` | O'rtacha (kun 3-5 ta) | **Ish uchun tavsiya** |
| `80.0` | Kam (kun 0-2 ta) | Tajribali treyderlar uchun |

> ⚠️ O'zgartirish uchun botni qayta yoqish kerak: `pkill -f bot.py && bash run.sh`

---
*Ushbu qo'llanma treyderga bozor mantiqini tushunishda va xavflarni boshqarishda yordam beradi.*

