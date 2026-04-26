# 🏛 GEMINI SMC TITAN V27.2 — Tizim Arxitekturasi

**Gemini SMC Titan V27.2** — uch qatlamli (Data, Analysis, Execution) modulli arxitektura bo'lib, Fibonacci, Engulfing, MTF filtr va SQLite doimiy xotira bilan jihozlangan.

---

## 1. Ma'lumotlar qatlami (Data Layer)

- **`exchange.py`**: Yahoo Finance, Binance va UzNEX (CCXT) orqali jonli narx va shamlar (OHLCV) ma'lumotlarini yuklaydi.
- **`watcher.py`**: `MarketWatcher` klassi orqali MTF trendlarini 30 daqiqalik keshda saqlaydi va `get_htf_trend()` bilan 1H EMA200 trendini aniqlaydi.
- **`persistence.py`**: Bot holatini (narxlar, loss_streak) JSON faylda saqlaydi — restart'dan keyin tiklanadi.
- **`price_fetcher.py`**: Real vaqtda (yfinance orqali) instrumentlar narxini oluvchi AI Tool.

---

## 2. Analiz qatlami (Analysis Layer)

- **`indicator.py`**: `GeminiIndicator` klassi — SMC (BOS, CHoCH, Order Block, FVG) va Fibonacci (0.618-0.786) logikasini hisoblaydi. Signal sifati 0-120 ball oralig'ida baholanadi.
- **`position_sizer.py`**: 2% risk qoidasi asosida optimal lot/coin miqdorini hisoblaydi. Barcha asosiy instrumentlar (XAU, Forex, Crypto) qo'llab-quvvatlanadi.
- **`ai_engine.py`**: `AIEngine` klassi — Google Gemini 1.5 Flash modeli orqali texnik, fundamental, scalping va chat tahlillarini amalga oshiradi. Multi-API key rotatsiyasi va Real-time Price (Function Calling) tizimi mavjud.
- **`rag_engine.py`**: PDF darsliklardan bilim qidiruvchi RAG (Retrieval-Augmented Generation) tizimi.
- **`chart_generator.py`**: `mplfinance` yordamida olingan ma'lumotlar asosida grafik tasvirlarni generatsiya qiladi.

### Signal Sifati Tizimi (Quality Score):
```
Boshlang'ich: 50 ball
+ EMA Trend (200+50):    +15
+ RSI Filtr:             +10
+ Hajm Tasdiqi:          +10
+ Sham Kuchi:            + 5
+ BOS Aniqlandi:         +15
+ FVG Mavjud:            + 5
+ Fibonacci 0.618 zona:  +10
─────────────────────────────
Maksimal:                120 ball
Standart chegara:        75.0  (settings.yaml da o'zgartirish mumkin)
```

---

## 3. Ijro va Boshqaruv qatlami (Execution & Management Layer)

- **`manager.py`**: `TradeManager` klassi — Savdo hayotiy siklini boshqaradi. **Risk Splitting** (2% riskni 0.5/0.382 Fibo darajalariga bo'lish) va **Feedback Loop** (SL dan so'ng `loss_streak` oshiriladi, sifat talabi avtomatik ko'tariladi) amalga oshiriladi.
- **`telegram.py`**: `TelegramNotifier` klassi — Masofaviy boshqaruv, AI Chat, signal yuborish va foydalanuvchi huquqlarini (admin/user) boshqaradi.
- **`analytics.py`**: So'nggi 50 ta signal statistikasini matnli hisobotga aylantiradi (AI tahlili uchun).
- **`dashboard.py`**: Flask orqali professional monitoring terminalini ishga tushiradi — **faqat lokal muhitda** (PA da o'chiriladi).
- **`mt5_signal.py`**: MetaTrader 5 Execution moduli — hozirda `mt5.enabled: false` sozlamasi bilan o'chirilgan.
- **`sms.py`**: Muvaffaqiyatli signallar va xatoliklar bo'yicha SMS yuborish mantiqi.
- **`tradingview.py`**: TradingView xizmatidan norasmiy API orqali texnik ma'lumotlarni o'qib olish.
- **`websocket_client.py`**: Binancedan real vaqtda ticker ma'lumotlarini oqim (stream) ko'rinishida olish mantiqi.

---

## 💾 Ma'lumotlar bazasi (Database)

- **`database.py`**: `DatabaseManager` klassi — SQLite bazasini boshqaradi. 4 ta jadval:
  - `history` — Savdo tarixi
  - `signals` — Generatsiya qilingan signallar logi
  - `chat_history` — AI chat xotirasi (foydalanuvchi bo'yicha, max 15 ta)
  - `stats` — Bot statistikasi

---

## 📱 Foydalanuvchi Huquqlari

| Knopka | Admin | Oddiy Foydalanuvchi |
|---|---|---|
| 📊 Texnik Tahlil | ✅ | ✅ |
| 🌐 Fundamental | ✅ | ✅ |
| 💬 AI Chat | ✅ | ✅ |
| 📈 Hisobot | ✅ | ✅ |
| 📖 Qo'llanma | ✅ | ✅ |
| ⚡ Scalping AI | ✅ | ❌ |
| ⚖️ Risk Status | ✅ | ❌ |
| 🚨 PANIC CLOSE ALL | ✅ | ❌ |

---

## 🔄 Signal Generatsiya Sikli (V27.2)

```
[Har 3 daqiqa]
     ↓
Data Fetch (exchange.py)
     ↓
MTF Trend Check (watcher.py - 1H EMA200 kesh)
     ↓
SMC + Fibo Analysis (indicator.py)
→ Quality Score < 75 → O'tkazib yuborish
→ Quality Score ≥ 75 → Signal chiqadi
     ↓
Risk Splitting (manager.py - 1% + 1% kirish)
     ↓
Position Sizing (position_sizer.py - 2% qoida)
     ↓
Telegram Signal + SQLite Log (database.py)
     ↓
Feedback Correction (loss_streak yangilash)
```

**V27.2 Titan — To'liq modullashtirilgan, o'zini o'zi mukammallashtiruvchi terminal.** 🚀
