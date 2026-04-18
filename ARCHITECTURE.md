# 🏛 GEMINI SMC TITAN V27 — System Architecture (Fibo-Engulf Evolution)

**Gemini SMC Titan V27** — bu uch qatlamli (Data, Analysis, Execution) modulli arxitektura bo'lib, hozirda Fibonachchi va Engulfing strategiyalari bilan boyitilgan.

---

## 1. Ma'lumotlar qatlami (Data Layer)
- **`exchange.py`**: Yahoo Finance, Binance va UzNEX (CCXT) orqali jonli narx ("Price Action") va shamlar ("OHLCV") ma'lumotlarini yuklaydi.
- **`watcher.py`**: Market skanerini boshqaradi va Multi-Timeframe (MTF) trendlarini keshlaydi.

## 2. Analiz qatlami (Analysis Layer)
- **`indicator.py`**: SMC (BOS, CHoCH, Order Block, FVG) va yangi **Fibo-Engulf** logikasini hisoblaydi.
- **`MTF Trend Guard`**: 1H EMA200 dan yuqori TF trendini aniqlab, 15M dagi signallarni filtrlaydi.
- **`Gemini AI Advisor`**: Google Gemini (2.0/2.5) orqali texnik va fundamental holatni chuqur tahlil qiladi.

## 3. Ijro va Boshqaruv qatlami (Execution & Management Layer)
- **`manager.py`**: Savdo hayotiy siklini (Trade Lifecycle) boshqaradi. **Risk Splitting** (2% riskni 0.5/0.618 Fibo darajalariga bo'lish) va **Feedback Loop** (SL dan so'ng sifatni oshirish) mantiqini amalga oshiradi.
- **`mt5_signal.py`**: Lotni hisoblaydi va MetaTrader 5 terminaliga buyruq yuboradi.
- **`telegram.py`**: Masofaviy boshqaruv, AI Chat va signallarni Telegramga yo'llaydi.
- **`dashboard.py`**: Flask orqali professional monitoring terminalini ishga tushiradi.

---

## 💾 Ma'lumotlar bazasi (Database)
- **`database.py`**: SQLite bazasini boshqaradi. Bitimlar tarixi va AI chat kontekstini abadiy saqlaydi.

---

## 🔄 Yangilangan Savdo Sikli (V27 Lifecycle)
`Loop (15m)` -> `Data Fetch` -> `SMC + Fibo Analysis` -> `Success Rate Weights` -> `Risk Splitting (1%+1%)` -> `Direct API/MT5 Execution` -> `Feedback Correction`.

**V27 Titan — To'liq avtomatlashtirilgan, o'zini o'zi mukammallashtiruvchi terminal.** 🚀
