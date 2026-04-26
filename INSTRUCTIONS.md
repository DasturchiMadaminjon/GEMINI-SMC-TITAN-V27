# 📘 GEMINI SMC TITAN V27.2 — Yo'riqnoma (Trader Guide)

Siz hozirgina dunyo darajasidagi SMC savdo terminalini o'rnatdingiz. Ushbu qo'llanma sizga **Fibo-Engulf**, **MTF Filtr** va **Feedback Loop** imkoniyatlaridan foydalanishda yordam beradi.

---

## 🛠 1. Birinchi Sozlash

### `.env` fayli (asosiy):
```
GEMINI_API_KEY=kalitingiz_bu_yerga  # Bir nechta bo'lsa vergul bilan
TELEGRAM_BOT_TOKEN=bot_token
TELEGRAM_CHAT_ID=sizning_chat_id
```

### `config/settings.yaml`:
- **`smc.min_quality`**: Signal sifati chegarasi (standart: `75.0`)
- **`exchange.name`**: `"yahoo"` (kuzatuv), `"binance"` yoki `"uznex"` (real savdo)
- **`trend.fibo_split_enabled`**: `true` — 2% riskni ikkita kirish nuqtasiga bo'lish
- **`mt5.enabled`**: `false` — MT5 o'chirilgan

---

## ⚙️ 2. Signal Sifatini Boshqarish

`config/settings.yaml` faylida:
```yaml
smc:
  min_quality: 75.0   # ✅ STANDART — kuniga 3-5 ta signal
  # min_quality: 65.0 # ⚠️ KO'PROQ signal (test uchun)
  # min_quality: 80.0 # 🔒 FAQAT A+ signallar
```

| Qiymat | Signal soni | Foydalanish |
|---|---|---|
| `65.0` | Kun 10-15 ta | Test va o'rganish |
| `75.0` | Kun 3-5 ta | **Asosiy ish rejimi** |
| `80.0` | Kun 0-2 ta | Tajribali treyderlar |

> ⚠️ O'zgartirish uchun botni qayta yoqing: `pkill -f bot.py && bash run.sh`

---

## ⚖️ 3. Risk va Fibo Strategiyasi

- **2-Kirish Nuqtasi**: Bot avtomatik ravishda 2% riskni ikkita kirish (`signal.entry` va `0.382 Fibo`) nuqtasiga bo'ladi — bu "fill" narxini yaxshilaydi.
- **Feedback Loop**: Agar savdo SL bilan yopilsa, bot keyingi signal uchun sifat talabini avtomatik oshiradi (`loss_streak` orqali). Bu "stop hunt" holatlaridan himoya qiladi.
- **MTF Filtr**: 15M signali 1H EMA200 trendiga mos kelishini tekshiradi (kesh: 30 daqiqa).

---

## 📱 4. Telegram Knopkalari va Vazifalari

### Hammaga ochiq:
| Knopka | Vazifa |
|---|---|
| 📊 **Texnik Tahlil** | Tanlangan instrument uchun SMC (BOS, CHoCH, OB, FVG) tahlilini Gemini AI bilan bajaradi |
| 🌐 **Fundamental** | DXY, FED ritorikasi, NFP/CPI va geosiyosat ta'sirini tahlil qiladi |
| 💬 **AI Chat** | Istalgan savol yoki chart rasmi — AI javob beradi, rasm tahlil qiladi |
| 📈 **Hisobot** | So'nggi 50 ta signal statistikasini AI menejeri sifatida tahlil qiladi |
| 📖 **Qo'llanma** | Barcha knopkalar va vazifalar haqida darhol ma'lumotnoma (AI ishlatmaydi) |

### Faqat Admin:
| Knopka | Vazifa |
|---|---|
| ⚡ **Scalping AI** | M5/M15 taymfreymlarda tezkor Engulfing kirish rejasini beradi |
| ⚖️ **Risk Status** | Joriy hisob balansini ko'rsatadi |
| 🚨 **PANIC CLOSE ALL** | Favqulodda: barcha ochiq pozitsiyalarni yopadi |

---

## 💬 5. AI Chat bilan Muloqot

Bot har qanday savol va chartni qabul qiladi:
- `GOLD hozir qancha?` → Real vaqtda XAUUSD narxini olish (Tool calling)
- `XAUUSD tahlil qil` → 1H trend + 15M SMC tahlili (Avto-chart)
- Chart rasmi yuboring → OB, FVG, Liquidity tahlili
- `BTC narxi necha?` → Kriptovalyuta narxini aniqlash

---

## 🚨 6. Favqulodda Vaziyat (Emergency)

Agar bozorda to'satdan yangilik (NFP, FED, geosiyosiy) chiqsa:
- **Telegramda**: `🚨 PANIC CLOSE ALL` tugmasini bosing
- **PA terminalda**: `pkill -f bot.py` bilan darhol to'xtating

---

## 🔍 7. Xatoliklarni Tuzatish

| Muammo | Yechim |
|---|---|
| Bot javob bermaydi | `tail -50 ~/signal_v_27/logs/keeper.log` — log tekshiring |
| `SyntaxError` | PA ga noto'g'ri fayl ko'chirilgan — `bot.py` qayta yuklang |
| `DRAFT MODE` | `.env` dagi `GEMINI_API_KEY` eskirgan — yangi kalit oling |
| Signal kelmaydi | `min_quality: 65.0` ga tushiring yoki `exchange.name: yahoo` tekshiring |
| `exit 137` | PA da xotira tugagan — `pkill -f bot.py && bash run.sh` |

---

## 📁 8. Muhim Fayllar

| Fayl | Maqsadi |
|---|---|
| `.env` | API kalitlar (Gemini, Telegram) |
| `config/settings.yaml` | Barcha sozlamalar (min_quality, symbols, risk) |
| `data/bot_state.json` | Bot xotirasi (narxlar, loss_streak) |
| `logs/bot_data.db` | SQLite: signallar + chat tarixi |
| `logs/keeper.log` | Bot ishlash logi |

---

**V27.2 Titan — Treyderning eng aqlli va ishonchli yordamchisi.** 🚀
