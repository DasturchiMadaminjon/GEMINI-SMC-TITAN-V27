import os, asyncio, threading, logging, yaml, warnings, json
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from utils.persistence import load_state, save_state
from utils.exchange import ExchangeClient
from utils.telegram import TelegramNotifier
from utils.chart_generator import generate_chart_buffer
from utils.database import DatabaseManager       # ✅ #2,4: DB integratsiya
from core.watcher import MarketWatcher           # ✅ #3: MTF Guard
from core.manager import TradeManager
warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

class GeminiBot:
    def __init__(self):
        with open('config/settings.yaml', 'r') as f: self.cfg = yaml.safe_load(f)
        
        # API kalitlarini yig'ish ( .env VA config dan)
        load_dotenv()
        env_keys = os.getenv('GEMINI_API_KEY', '')
        
        # settings.yaml dagi kalitlarni ham o'qish (agar bo'lsa)
        self.api_keys = []
        raw_keys = self.cfg.get('gemini_ai', {}).get('api_keys', [])
        if isinstance(raw_keys, list): self.api_keys.extend(raw_keys)
        
        # .env dagi kalitlarni qo'shish (vergul bilan ajratilgan)
        if env_keys:
            self.api_keys.extend([k.strip() for k in env_keys.split(',') if len(k.strip()) > 20])
        
        self.api_keys = list(set(self.api_keys)) # Dublikatlarni olib tashlash
        
        # MUHIM: Kalitlarni config ichiga joylaymiz, chunki TelegramNotifier undan o'qiydi
        if 'gemini_ai' not in self.cfg: self.cfg['gemini_ai'] = {}
        self.cfg['gemini_ai']['api_keys'] = self.api_keys
        
        print(f"🔑 [AUTH] Gemini API kalitlari yuklandi: {len(self.api_keys)} ta")
        if len(self.api_keys) == 0:
            print("⚠️ [WARNING] Hech qanday API kalit topilmadi! .env faylini tekshiring.")
        
        self.bot_token = self.cfg.get('telegram', {}).get('bot_token') or os.getenv('TELEGRAM_BOT_TOKEN')
        self.cfg['telegram']['bot_token'] = self.bot_token
        
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
        self.telegram = TelegramNotifier(self.cfg, self.lock)
        self.exchange = ExchangeClient(self.cfg)
        self.db = DatabaseManager()                          # ✅ #2: SQLite ulanish
        self.watcher = MarketWatcher(self.cfg, self.exchange) # ✅ #3: MTF Guard
        self.trades = TradeManager(self.cfg, self.db, type('AlertManager', (), {'telegram': self.telegram}))
        self.trades.loss_streak = self.bot_state.get('loss_streak', 0)  # Restart'dan keyin tiklash
        print(f"💾 [DB] SQLite baza tayyor. loss_streak={self.trades.loss_streak}")

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

        if t == 'analytics':
            from utils.analytics import generate_trade_report
            with self.lock:
                prompt_text = generate_trade_report(self.bot_state)
            img = None # Analytics uses text data
            prompt = prompt_text
        else:
            prompts = {
                'technical':   f"Instrument: {s} | Joriy narx: {p}\nMana oxirgi 100 ta sham charti. SMC metodikasi asosida to'liq texnik tahlil ber.",
                'scalping':    f"Instrument: {s} | Joriy narx: {p}\nMana oxirgi 100 ta sham charti. M5/M15 uchun tezkor scalping kirish rejasini ber.",
                'fundamental': f"Instrument: {s} | Joriy narx: {p}\nFAQAT makro drayverlar (DXY, FED, yangiliklar) asosida fundamental tahlil qil. SMC aytma.",
                'chat':        f"{req.get('text', '')}{'  [Rasm yuborildi — chartni tahlil qil]' if img else ''}",
                'mentor_lessons':       f"{req.get('text', '')}",
                'mentor_qa':            f"{req.get('text', '')}" + (" [Rasm yuborilgan bo'lsa tahlil qil]" if img else ""),
                'mentor_live_examples': f"{req.get('text', '')}"
            }
            prompt = prompts.get(t, prompts['technical'])

        # Exponential Backoff: 503/429 bo'lsa 3 marta qayta urinish
        max_retries = 3
        res = "" # Bo'sh qoldiramiz
        
        for attempt in range(max_retries):
            try:
                res = await self.telegram.get_ai_analysis(prompt, uid, context=t, image_data=img)
                
                # Agar AI javobi xato haqida bo'lsa (leaked key kabi), qayta urinib o'tirmaymiz
                if "❌ XATO" in res or "❌ API" in res:
                    break 

                # Agar AI Draft qaytarsa va bu oxirgi urinish bo'lmasa, qayta urinishni chaqiramiz
                if "DRAFT" in res and attempt < max_retries - 1:
                    raise Exception("429 API Band (Draft qaytdi)")
                    
                break  # Muvaffaqiyatli — to'xtaymiz
            except Exception as e:
                err = str(e)
                if "503" in err or "429" in err:
                    wait = (attempt + 1) * 3
                    logger.warning(f"AI Busy. Attempt {attempt+1}/{max_retries}. Wait {wait}s...")
                    await asyncio.sleep(wait)
                    res = f"⚠️ Server hozircha band (Attempts: {attempt+1})"
                else:
                    res = f"❌ AI Tizim Xatoligi: {err[:150]}"
                    break
        
        if not res:
            res = "⚠️ AI tizimiga ulanib bo'lmadi. Kalitlarni tekshiring."

        # ✅ #4: AI chat tarixini DB ga saqlash
        if t == 'chat':
            user_msg = req.get('text', '')
            if user_msg:
                self.db.add_chat_message(uid, 'user', user_msg)

        await self.telegram.send(f"🤖 <b>AI {t.upper()} TAHLILI ({s}):</b>\n\n{res}", cid=uid)

        # ✅ #4: AI javobini ham DB ga saqlash
        if t == 'chat' and res and '❌' not in res:
            self.db.add_chat_message(uid, 'assistant', res[:500])

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
        main_kb = {'keyboard': [
            [{'text': "📊 Texnik Tahlil"}, {'text': "🌐 Fundamental"}],
            [{'text': "👨‍🏫 Jonli SMC Trener"}, {'text': "💬 AI Chat Assistant"}],
            [{'text': "⚡ Scalping AI"}, {'text': "📈 Hisobot (Analytics)"}],
            [{'text': "⚖️ Risk Status"}, {'text': "🚨 PANIC CLOSE ALL"}],
            [{'text': "📖 Qo'llanma"}]
        ], 'resize_keyboard': True}
        await self.telegram.send(start_msg, kb=json.dumps(main_kb))
        
        print("🚀 Titan V27.2 A+ MASTER ENGINE IS LIVE!")
        
        while True:
            for s in self.cfg['symbols']:
                print(f"🔍 [SCANNER] {s} tekshirilmoqda...")
                df = self.exchange.fetch_ohlcv(s, self.cfg.get('timeframe', '15m'), limit=200)
                if df is not None:
                    curr_p = float(df['close'].iloc[-1])

                    # ✅ #3: MTF HTF trend ni kesh orqali olish
                    htf_trend = self.watcher.get_cached_trend(s)
                    if htf_trend is None:
                        try:
                            htf_trend = self.watcher.get_htf_trend(s)
                            if htf_trend:
                                self.watcher.update_mtf_cache(s, htf_trend, self.lock)
                        except Exception:
                            htf_trend = None

                    with self.lock:
                        self.bot_state['symbols'][s]['price'] = curr_p
                        if htf_trend:
                            self.bot_state['symbols'][s]['htf_trend'] = htf_trend
                        self.bot_state['loss_streak'] = self.trades.loss_streak  # ✅ #2
                        save_state(self.bot_state)

                    # ✅ #2: Signal chiqsa DB ga yozish
                    from core.indicator import GeminiIndicator
                    ind = GeminiIndicator(self.cfg)
                    sig = ind.generate_signal(df, s, self.cfg.get('timeframe', '15m'), self.trades.loss_streak)
                    if sig:
                        now_str = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')
                        self.db.add_signal(now_str, s, sig.direction, sig.entry, int(sig.quality), sig.reason)

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
    
    # Dashboardni faqat lokalda yoqamiz (Serverda u xalaqit beradi)
    is_pa = "PYTHONANYWHERE_DOMAIN" in os.environ
    if not is_pa:
        try:
            from utils.dashboard import create_app
            import threading
            flask_app = create_app(bot_app.bot_state, bot_app.cfg, bot_app.lock)
            def run_flask():
                flask_app.run(host="0.0.0.0", port=8080, debug=False, use_reloader=False)
            threading.Thread(target=run_flask, daemon=True).start()
            print("--> Localhost Dashboard ishga tushdi -> http://127.0.0.1:8080")
        except Exception as e:
            print(f"⚠️ Dashboard ogohlantirishi: {e}")

    # Botning asosiy halqasi (Asyncio) ishga tushadi
    print(f"🚀 Titan V27.2 A+ MASTER ENGINE IS LIVE! (Server: {'PA' if is_pa else 'Local'})")
    try:
        asyncio.run(bot_app.run())
    except KeyboardInterrupt:
        print("\n🛑 Bot to'xtatildi.")
    except Exception as e:
        print(f"❌ Kutilmagan global xato: {e}")
