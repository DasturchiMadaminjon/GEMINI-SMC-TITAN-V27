# 📘 GEMINI SMC TITAN V27 — Yo'riqnoma (Trader Guide)

Siz hozirgina dunyodagi eng kuchli SMC savdo terminalini o'rnatdingiz. Ushbu qo'llanma sizga yangi **Fibo-Engulf** va **Feedback Loop** imkoniyatlaridan foydalanishda yordam beradi.

---

## 🛠 1. Fundamental Sozlash (Config)
**`config/settings.yaml`** faylini oching:
-   **`exchange`**: `name: "uznex"` yoki `"binance"` qilib, API kalitlaringizni kiriting.
-   **`fibo_split_enabled`**: `true` qilib qoldiring (2% riskni 0.5/0.618 darajalariga bo'lish uchun).
-   **`gemini_ai`**: `model: "gemini-2.0-flash"` modelini tanlang.

---

## ⚖️ 2. Risk Management & Fibo (Xavfsizlik)
Professional treyderlar uchun yangi qoidalar:
-   **Fibo Entries**: Bot avtomatik ravishda 2% riskni ikkita 1% li kirish nuqtalariga bo'ladi. Bu sizning "Entry filling" narxingizni yaxshilaydi.
-   **Feedback Loop**: Agar savdo SL (Stop Loss) bilan yopilsa, bot keyingi signal uchun sifat talabini avtomatik oshiradi. Bu sizni bozordagi "qopqonlar"dan (Stop Hunts) himoya qiladi.
-   **EMA 200 (MTF Trend)**: `higher_tf: "1h"` qilib qoldiring. Trendga qarshi savdo qilmaslik win-rate ni oshiradi.

---

## 💬 3. AI Chat bilan Muloqot
Telegram orqali botga istalgan savolizni bera olasiz:
-   `GOLD hozir qanday holatda?` — Bot 1H trendini va 15M dagi SMC + Fibo holatini ko'rib javob beradi.
-   `Fibo-Engulf signallarini ko'rsat?` — Bot barcha simvollar bo'yicha eng yangi Fibo setup'larini scan qiladi.

---

## 🚨 4. Emergency (Panic Button)
Agar bozorda to'satdan kutilmagan yangilik (NFP, Interest Rates) chiqsa:
-   **Dashboardda** `EMERGENCY CLOSE ALL` tugmasini bosing.
-   **Telegramda** `🚨 PANIC CLOSE` tugmasini bosing.
-   Bot barcha ochiq va kutishdagi (pending) buyruqlarni bir soniyada yopadi.

---

## 🔍 Troubleshooting (Xatoliklarni tuzatish)
-   **UzNEX xatosi:** `pip install --upgrade ccxt` buyrug'i orqali kutubxonani yangilang.
-   **MT5 ulanmasa:** Broker serveringiz nomi va parolingiz to'g'riligini tekshiring.
-   **AI xato bersa:** API kalitingiz Google AI Studio'da faol ekanligini tasdiqlang.

**V27 Titan — Treyderning eng aqlli yordamchisi.** 🚀
