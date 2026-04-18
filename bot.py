import os, asyncio, threading, logging, yaml, warnings, json
from datetime import datetime, timezone, timedelta
from utils.persistence import load_state, save_state
from utils.exchange import ExchangeClient
from utils.telegram import TelegramNotifier
from utils.chart_generator import generate_chart_buffer
from core.manager import TradeManager
warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.ERROR)

class GeminiBot:
    def __init__(self):
        with open('config/settings.yaml', 'r') as f: self.cfg = yaml.safe_load(f)
        
        # Multi-API Support: List yoki bitta stringni o'qish
        gem_cfg = self.cfg.get('gemini_ai', {})
        raw_keys = gem_cfg.get('api_keys', []) # List ko'rinishida: ["KEY1", "KEY2"]
        single_key = gem_cfg.get('api_key') or os.getenv('GEMINI_API_KEY')
        
        # Barcha kalitlarni bitta ro'yxatga yig'ish
        self.api_keys = []
        if isinstance(raw_keys, list): self.api_keys.extend(raw_keys)
        if single_key: self.api_keys.append(single_key)
        self.api_keys = list(set(self.api_keys)) # Dublikatlarni olib tashlash
        
        self.cfg['gemini_ai']['api_keys'] = self.api_keys
        
        self.bot_token = self.cfg.get('telegram', {}).get('bot_token') or os.getenv('TELEGRAM_BOT_TOKEN')
        self.cfg['telegram']['bot_token'] = self.bot_token
        
        # Xotirani yuklash (Memory Persistence)
        saved = load_state()
        self.bot_state = saved if saved else {
            'symbols': {},
            'terminal': {'balance': 5000.0}, 'ai_requests': [], 'loss_streak': 0
        }
        
        # Yangi simvollarni xotiraga qo'shish (Sinxronizatsiya)
        for s in self.cfg['symbols']:
            if s not in self.bot_state['symbols']:
                self.bot_state['symbols'][s] = {'price': 0.0}

        # Restart da eski navbatni tozalash (dublikat xabarlar oldini olish)
        self.bot_state['ai_requests'] = []
        save_state(self.bot_state)

        self.lock = threading.Lock()
        self.telegram = TelegramNotifier(self.cfg, self.lock) # TelegramNotifier o'zi AIEnginega uzatadi
        self.exchange = ExchangeClient(self.cfg)
        self.trades = TradeManager(self.cfg, None, type('AlertManager', (), {'telegram': self.telegram}))
        self.trades.loss_streak = self.bot_state.get('loss_streak', 0)

    async def _handle_ai(self, req):
        uid = req['chat_id']; s = req['symbol']; t = req['type']
        p = self.bot_state['symbols'].get(s, {}).get('price', 0)
        img = req.get('image')
        
        # Avtomatik Chart generatsiyasi — Technical va Scalping uchun AI ko'zi
        if not img and t in ['technical', 'scalping']:
            try:
                loop = asyncio.get_event_loop()
                df = await loop.run_in_executor(None, self.exchange.fetch_ohlcv, s, self.cfg.get('timeframe', '15m'), 100)
                if df is not None and not df.empty:
                    img = await generate_chart_buffer(df)
            except Exception as e:
                print(f"DEBUG: Avto-chart xatosi: {e}")

        await self.telegram.send_action(uid, "upload_photo" if img else "typing")

        prompts = {
            'technical':   f"Instrument: {s} | Joriy narx: {p}\nMana oxirgi 100 ta sham charti. SMC metodikasi asosida to'liq texnik tahlil ber.",
            'scalping':    f"Instrument: {s} | Joriy narx: {p}\nMana oxirgi 100 ta sham charti. M5/M15 uchun tezkor scalping kirish rejasini ber.",
            'fundamental': f"Instrument: {s} | Joriy narx: {p}\nFAQAT makro drayverlar (DXY, FED, yangiliklar) asosida fundamental tahlil qil. SMC aytma.",
            'chat':        f"{req.get('text', '')}{'  [Rasm yuborildi — chartni tahlil qil]' if img else ''}"
        }
        
        prompt = prompts.get(t, prompts['technical'])

        # Exponential Backoff: 503/429 bo'lsa 3 marta qayta urinish
        max_retries = 3
        res = "⚠️ Server vaqtincha band. Keyinroq urinib ko'ring."
        for attempt in range(max_retries):
            try:
                res = await self.telegram.get_ai_analysis(prompt, uid, context=t, image_data=img)
                
                # Agar AI Draft qaytarsa va bu oxirgi urinish bo'lmasa, qayta urinishni chaqiramiz
                if "DRAFT" in res and attempt < max_retries - 1:
                    raise Exception("429 API Band (Draft qaytdi)")
                    
                break  # Muvaffaqiyatli — to'xtaymiz
            except Exception as e:
                err = str(e)
                if "503" in err or "429" in err:
                    wait = (attempt + 1) * 5  # 5s → 10s → 15s
                    print(f"⚠️ [{t.upper()}] API band. {attempt+1}-urinish. {wait}s kutamiz...")
                    await asyncio.sleep(wait)
                else:
                    res = f"❌ API Xatoligi: {err[:200]}"
                    break

        await self.telegram.send(f"🤖 <b>AI {t.upper()} TAHLILI ({s}):</b>\n\n{res}", cid=uid)

    async def _ai_loop(self):
        """AI so'rovlarini qayta ishlash loopi (A+ Master)"""
        while True:
            reqs = []
            with self.lock:
                if self.bot_state.get('ai_requests'):
                    reqs = self.bot_state['ai_requests']
                    self.bot_state['ai_requests'] = []
            
            for i, r in enumerate(reqs):
                try: await self._handle_ai(r)
                except Exception as e: logger.error(f"AI Handle error: {e}")
                # Ketma-ket so'rovlar orasida 3 soniya kutish (Rate limit oldini olish)
                if i < len(reqs) - 1:
                    await asyncio.sleep(3)
            
            await asyncio.sleep(2)

    async def _market_loop(self):
        # Startup Message
        now_utc = datetime.now(timezone.utc)
        now_uzb = now_utc + timedelta(hours=5)
        
        start_msg = (
            "🚀 <b>GEMINI SMC TITAN V27 — Ishga tushdi</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"📊 Instrumentlar: {', '.join(self.cfg['symbols'])}\n"
            f"⏱️ Timeframe: {self.cfg.get('timeframe', '15m')}\n"
            f"🕐 Vaqt (UTC): {now_utc.strftime('%d.%m.%Y %H:%M')}\n"
            f"🇺🇿 Vaqt (UZB): {now_uzb.strftime('%d.%m.%Y %H:%M')}\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "Signal kutilmoqda..."
        )
        
        # Klaviaturani startup xabari bilan yuborish
        main_kb = {'keyboard': [[{'text': "📊 Texnik Tahlil"}, {'text': "🌐 Fundamental"}],[{'text': "⚡ Scalping AI"}, {'text': "💬 AI Chat Assistant"}],[{'text': "⚖️ Risk Status"}, {'text': "📖 Qo'llanma"}],[{'text': "🚨 PANIC CLOSE ALL"}]], 'resize_keyboard': True}
        await self.telegram.send(start_msg, kb=json.dumps(main_kb))
        
        print("🚀 Titan V27.2 A+ MASTER ENGINE IS LIVE!")
        
        while True:
            for s in self.cfg['symbols']:
                print(f"🔍 [SCANNER] {s} tekshirilmoqda...")
                df = self.exchange.fetch_ohlcv(s, self.cfg.get('timeframe', '15m'), limit=200)
                if df is not None:
                    curr_p = float(df['close'].iloc[-1])
                    with self.lock: 
                        self.bot_state['symbols'][s]['price'] = curr_p
                        self.bot_state['loss_streak'] = self.trades.loss_streak
                        save_state(self.bot_state) # Holatni saqlash
                    self.trades.process_symbol_data(s, df, self.bot_state, self.lock, 0)
                await asyncio.sleep(10)
            print("⏳ [SYSTEM] Skanerlash yakunlandi. 3 daqiqa kutish...")
            await asyncio.sleep(180)

    async def run(self):
        await asyncio.gather(
            self.telegram.poll_updates(self.bot_state), 
            self._market_loop(),
            self._ai_loop()
        )

if __name__ == "__main__":
    bot_app = GeminiBot()
    
    # 🌐 Localhost Dashboard (Web Sayt) Motorini qoshish va yoqish
    from utils.dashboard import create_app
    import threading
    
    flask_app = create_app(bot_app.bot_state, bot_app.cfg, bot_app.lock)
    
    def run_flask():
        flask_app.run(host="0.0.0.0", port=8080, debug=False, use_reloader=False)
        
    dashboard_thread = threading.Thread(target=run_flask, daemon=True)
    dashboard_thread.start()
    print("--> Localhost Dashboard ishga tushdi -> Kiring: http://127.0.0.1:8080")

    # Botning asosiy halqasi (Asyncio) ishga tushadi
    try:
        asyncio.run(bot_app.run())
    except KeyboardInterrupt:
        print("\n🛑 Bot va Localhost to'xtatildi.")
