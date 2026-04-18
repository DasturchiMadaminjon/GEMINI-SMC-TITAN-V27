# 🚀 GEMINI SMC TITAN V27 — Professional Terminal Suite (Fibo-Engulf Edition)

**Gemini SMC Titan V27** — dunyo bo'yicha eng kuchli SMC (Smart Money Concepts) logikasi asosida yaratilgan, Gemini AI va MT5/UzNEX bilan integratsiya qilingan savdo terminali.

---

## 🌟 V27 Titan — Yangi imkoniyatlar:
- ✅ **Fibo-Engulf Entry** — Engulfing shamini aniqlash va 0.5/0.618 Fibonachchi darajalariga avtomatik limit orderlar qo'yish.
- ✅ **2% Risk Split** — Jami 2% riskni ikkita 1% li kirish nuqtalariga (0.5 va 0.618) bo'lish orqali kirish narxini (fill) optimallashtirish.
- ✅ **Professional Feedback Loop** — Har bir Stop-Loss (SL) dan so'ng, bot avtomatik ravishda keyingi signal uchun sifat (minQuality) talabini oshiradi.
- ✅ **Direct Exchange Execution** — UzNEX va Binance birjalari bilan to'g'ridan-to'g'ri API orqali savdo qilish.
- ✅ **MTF Trend Guardian** — 15M signalini 1H ema200 trendi bilan tasdiqlash.

---

## 📂 Arxitektura Tuzilmasi:
```
gemini_bot/
├── bot.py                  ← Tizim boshqaruv markazi va Looplar (Market, AI, Terminal)
├── core/
│   ├── indicator.py        ← SMC Analiz O'zagi, Engulfing + Fibonacci mantiqi
│   └── manager.py          ← Savdo boshqaruvi, Risk Splitting va Feedback Loop
├── utils/
│   ├── database.py         ← SQLite Baza (Bitimlar va AI chat xotirasi)
│   ├── dashboard.py        ← Professional Web Terminal (Localhost:8080)
│   ├── mt5_signal.py       ← MT5 Execution va Lot Calculation
│   ├── telegram.py         ← AI Chat va Remote Control (Signals)
│   └── exchange.py         ← Yahoo/Binance/UzNEX Market Data va Order Client
└── bilim_bazasi/            ← Strategiya qo'llanmalari (PDF va darsliklar)
```

---

## ⚡ Ishga tushirish (Setup Guide):
1. Kutubxonalarni yangilash: `pip install -r requirements.txt` (muhim: ccxt>=4.2.0)
2. Sozlash: `/config/settings.yaml` da API kalit va MT5/Exchange ma'lumotlarini to'ldiring.
3. Start: `python bot.py`

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
Dastur **Google Gemini 2.0 Flash** modeliga integratsiya qilingan. 
*   **AI foydasi**: U shunchaki grafikdagi chiziqlarni emas, balki "market sentiment"ni tushunadi. 
*   **Bilim Bazasi**: Botning algoritmi ichiga professional SMC darsliklari va Fibo-Engulfing qoidalari kodlangan bo'lib, u bilimlarni har bir signalda qo'llaydi.

---
*Ushbu qo'llanma treyderga bozor mantiqini tushunishda va xavflarni boshqarishda yordam beradi.*

