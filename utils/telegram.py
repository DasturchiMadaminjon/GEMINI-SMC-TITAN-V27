import logging, asyncio, aiohttp, json, os, random, yaml
from utils.ai_engine import AIEngine

logger = logging.getLogger(__name__)

class TelegramNotifier:
    def __init__(self, config, lock):
        self.cfg = config['telegram']; self.lock = lock
        is_pa = "PYTHONANYWHERE_DOMAIN" in os.environ
        self.proxy = "http://proxy.server:3128" if is_pa else None
        self.base = f"https://api.telegram.org/bot{self.cfg['bot_token']}"
        self.admins = [str(x).strip() for x in self.cfg.get('chat_id', [])]
        self.api_keys = config.get('gemini_ai', {}).get('api_keys', [])
        self.model_name = config.get('gemini_ai', {}).get('model', 'gemini-1.5-flash')
        self.ai = AIEngine(self.api_keys, self.model_name)
        self._session = None
        
        # --- FSM (Holatlar va Xotira) ---
        self.user_states = {}  
        self.user_modules = {} 

    async def get_session(self):
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=45))
        return self._session

    async def send(self, t, cid=None, kb=None):
        """Robust Message Sender with 503 Retry"""
        sess = await self.get_session()
        cids = [cid] if cid else self.admins
        for c in cids:
            for i in range(0, len(str(t)), 4000):
                chunk = t[i:i+4000]
                data = {'chat_id': c, 'text': chunk, 'parse_mode': 'HTML'}
                if kb and i == 0: data['reply_markup'] = kb
                
                for attempt in range(3):
                    try:
                        async with sess.post(f"{self.base}/sendMessage", proxy=self.proxy, json=data) as r:
                            if r.status == 200: break
                            elif r.status in (502, 503, 504): # Gateway/Proxy Errors
                                print(f"DEBUG: {r.status} Error (SendMessage), retrying {attempt+1}/3...")
                                await asyncio.sleep(1.5)
                            else: break
                    except: 
                        await asyncio.sleep(1)
                await asyncio.sleep(0.3)

    async def send_action(self, cid, action="typing"):
        """Robust Action Sender with 503 Retry"""
        sess = await self.get_session()
        for attempt in range(2):
            try:
                async with sess.post(f"{self.base}/sendChatAction", proxy=self.proxy, json={'chat_id': cid, 'action': action}) as r:
                    if r.status == 200: return True
                    elif r.status in (502, 503, 504): await asyncio.sleep(1)
            except: pass
        return False

    async def get_ai_analysis(self, p, chat_id, context="technical", image_data=None):
        return await self.ai.get_analysis(p, context, image_bytes=image_data)

    async def poll_updates(self, bs):
        # Offset ni diskdan tiklash (Restart'dan keyin dublikat oldini olish)
        off = 0
        off_file = ".tg_offset"
        try:
            if os.path.exists(off_file):
                with open(off_file) as f:
                    off = int(f.read().strip() or 0)
        except: off = 0

        with open('config/settings.yaml', 'r') as f:
            cfg_full = yaml.safe_load(f)
            sym_list = cfg_full.get('symbols', ["XAU/USD", "BTC/USDT"])
            
        while True:
            try:
                sess = await self.get_session()
                async with sess.get(f"{self.base}/getUpdates?offset={off+1}&timeout=30", proxy=self.proxy) as r:
                    if r.status != 200:
                        if r.status in (502, 503, 504):
                            await asyncio.sleep(2) # Proksi xatosi bo'lsa tezroq qayta urinish
                        else:
                            await asyncio.sleep(5)
                        continue
                    
                    res = await r.json()
                    for u in res.get('result', []):
                        off = u['update_id']; m = u.get('message', {}); cb = u.get('callback_query', {})
                        uid = str(cb.get('from', m.get('from', {})).get('id', ''))

                        # Offset darhol diskka yozish (keyingi restart uchun)
                        try:
                            with open(off_file, 'w') as f: f.write(str(off))
                        except: pass

                        if cb:
                            d = cb['data']
                            # --- SMC Trener Inline Mantiqi (FSM kesh orqali) ---
                            if d.startswith("mentor_"):
                                if d == "mentor_exit":
                                    self.user_states.pop(uid, None)
                                    self.user_modules.pop(uid, None)
                                    await sess.post(f"{self.base}/sendMessage", proxy=self.proxy, json={'chat_id': uid, 'text': "🚪 Trener rejimidan chiqdingiz. Asosiy menyudasiz."})
                                else:
                                    self.user_states[uid] = "in_session"
                                    self.user_modules[uid] = d
                                    if d == "mentor_lessons": text = "📚 <b>Mavzuli Darslar</b> faollashdi.\n\nSMC asoslari bo'yicha qaysi mavzudan boshlaymiz?"
                                    elif d == "mentor_live_examples": text = "🌐 <b>Jonli Misollar</b> faollashdi.\n\nHozirgi bozor yangiliklari va holatini tahlil qilamiz. Savolingizni yo'llang:"
                                    elif d == "mentor_qa": text = "❓ <b>Erkin Savol-Javob</b> faollashdi.\n\nSMC bo'yicha istalgan savolingizni bering:"
                                    else: text = "Noma'lum modul tanlandi."
                                    
                                    await sess.post(f"{self.base}/sendMessage", proxy=self.proxy, json={'chat_id': uid, 'text': text, 'parse_mode': 'HTML'})
                                
                                try: await sess.post(f"{self.base}/answerCallbackQuery", proxy=self.proxy, json={'callback_query_id': cb['id']})
                                except: pass
                                continue

                            # Faqat Scalping inline knopkasi adminlar uchun
                            if d.startswith("ai_scalping") and uid not in self.admins:
                                await sess.post(f"{self.base}/answerCallbackQuery", proxy=self.proxy, json={'callback_query_id': cb['id'], 'text': "❌ Scalping faqat adminlar uchun.", 'show_alert': True})
                                continue

                            if d.startswith("ai_"):
                                t, s = d.replace("ai_","").split(":")
                                with self.lock: bs['ai_requests'].append({'type': t, 'symbol': s, 'chat_id': uid})
                                await self.send(f"⏳ <i>{s} uchun {t.upper()} tahlili tayyorlanmoqda...</i>", cid=uid)
                                try: await sess.post(f"{self.base}/answerCallbackQuery", proxy=self.proxy, json={'callback_query_id': cb['id']})
                                except: pass

                        elif m:
                            t = m.get('text', '')
                            is_admin = uid in self.admins
                            ADMIN_KB = {'keyboard': [
                                [{'text': "📊 Texnik Tahlil"}, {'text': "🌐 Fundamental"}],
                                [{'text': "👨‍🏫 Jonli SMC Trener"}, {'text': "💬 AI Chat Assistant"}],
                                [{'text': "⚡ Scalping AI"}, {'text': "📈 Hisobot (Analytics)"}],
                                [{'text': "⚖️ Risk Status"}, {'text': "🚨 PANIC CLOSE ALL"}],
                                [{'text': "📖 Qo'llanma"}]
                            ], 'resize_keyboard': True}
                            USER_KB  = {'keyboard': [
                                [{'text': "📊 Texnik Tahlil"}, {'text': "🌐 Fundamental"}],
                                [{'text': "👨‍🏫 Jonli SMC Trener"}, {'text': "💬 AI Chat Assistant"}],
                                [{'text': "📈 Hisobot (Analytics)"}, {'text': "📖 Qo'llanma"}]
                            ], 'resize_keyboard': True}

                            # --- 1. Izolyatsiya qilingan FSM tekshiruvi (Trener in session) ---
                            current_state = self.user_states.get(uid)
                            if current_state == "in_session":
                                if t and t.lower() in ["chiqish", "exit", "stop", "/start"]:
                                    self.user_states.pop(uid, None)
                                    self.user_modules.pop(uid, None)
                                    kb = ADMIN_KB if is_admin else USER_KB
                                    await sess.post(f"{self.base}/sendMessage", proxy=self.proxy, json={'chat_id': uid, 'text': "🚪 Trener rejimidan chiqdingiz.", 'reply_markup': kb})
                                    continue
                                
                                module = self.user_modules.get(uid, "mentor_qa")
                                img_data = None
                                if m.get('photo'):
                                    fid = m['photo'][-1]['file_id']
                                    try:
                                        async with sess.get(f"{self.base}/getFile?file_id={fid}", proxy=self.proxy) as gr:
                                            if gr.status == 200:
                                                fpath = (await gr.json())['result']['file_path']
                                                async with sess.get(f"https://api.telegram.org/file/bot{self.cfg['bot_token']}/{fpath}", proxy=self.proxy) as dr:
                                                    if dr.status == 200: img_data = await dr.read()
                                    except: pass

                                # Hozircha Local fayldan matn olishni mock (simulyatsiya) qilamiz va AIEnginiga tashlaymiz
                                await self.send(f"🧠 [Trener tahlil qilmoqda...]", cid=uid)
                                with self.lock: bs['ai_requests'].append({
                                    'type': module, 'symbol': 'SMC KNOWLEDGE',
                                    'chat_id': uid, 'text': t or m.get('caption', ''), 'image': img_data
                                })
                                continue

                            # --- 2. Asosiy Menyular logikasi ---
                            if t == "👨‍🏫 Jonli SMC Trener":
                                self.user_states[uid] = "choosing_module"
                                ikb = {'inline_keyboard': [
                                    [{'text': "📚 Mavzuli Darslar", 'callback_data': "mentor_lessons"}],
                                    [{'text': "🌐 Jonli Misollar", 'callback_data': "mentor_live_examples"}],
                                    [{'text': "❓ Erkin Savol-Javob", 'callback_data': "mentor_qa"}],
                                    [{'text': "🚪 Trenerdan chiqish", 'callback_data': "mentor_exit"}]
                                ]}
                                await self.send("👨‍🏫 <b>Jonli SMC Trener</b> rejimiga xush kelibsiz!\n\nBu yerda siz SMC va bozor tuzilishi bo'yicha ta'lim olasiz.\nYo'nalishni tanlang:", cid=uid, kb=json.dumps(ikb))
                                continue

                            if t == "/start":
                                self.user_states.pop(uid, None)
                                self.user_modules.pop(uid, None)
                                kb = ADMIN_KB if is_admin else USER_KB
                                await sess.post(f"{self.base}/sendMessage", proxy=self.proxy, json={'chat_id': uid, 'text': "<b>V27.2 A+ TITAN MASTER</b>", 'reply_markup': kb, 'parse_mode': 'HTML'})

                            elif any(x in t for x in ["Tahlil", "Fundamental", "Scalping"]):
                                # Scalping faqat admin
                                if "Scalp" in t and not is_admin:
                                    await self.send("❌ Scalping faqat Admin uchun.", cid=uid)
                                    continue
                                type_ai = 'fundamental' if 'Fund' in t else ('scalping' if 'Scalp' in t else 'technical')
                                ikb = {'inline_keyboard': [[{'text': s, 'callback_data': f"ai_{type_ai}:{s}"}] for s in sym_list]}
                                await self.send("🔍 Instrumentni tanlang:", cid=uid, kb=json.dumps(ikb))

                            elif any(x in t.upper() for x in ["PANIC", "RISK", "STATUS"]):
                                # PANIC va RISK faqat admin
                                if is_admin:
                                    if "PANIC" in t.upper():
                                        await self.send("🚨 <b>EMERGENCY CALLED!</b>", cid=uid)
                                        with self.lock: bs['panic_request'] = True
                                    else:
                                        with self.lock: b = bs['terminal']['balance']
                                        await self.send(f"⚖️ <b>Balance: ${b}</b>", cid=uid)

                            elif any(x in t for x in ["Hisobot", "Analytics"]):
                                # Hisobot — hammaga ochiq
                                with self.lock: bs['ai_requests'].append({'type': 'analytics', 'symbol': 'KNOWLEDGE_BASE', 'chat_id': uid, 'text': 'Iltimos, Analytics moduligacha xulosa bering.'})
                                await self.send("📈 <i>Fayllardan loglar yig'ilmoqda... Fonda AI siz uchun yozma hisobot tuzmoqda...</i>\n(Bu odatda 15 soniya atrofida vaqt oladi)", cid=uid)

                            elif any(x in t for x in ["Chat Assistant", "💬 AI Chat"]):
                                # Chat assistant — hammaga ochiq
                                await self.send("💬 Savol yoki rasm (chart) yuboring.", cid=uid)

                            elif "Qo'llanma" in t or "qo'llanma" in t.lower():
                                # 📖 Qo'llanma — hammaga ochiq
                                guide = (
                                    "📖 <b>GEMINI SMC TITAN V27.2 — Qo'llanma</b>\n"
                                    "━━━━━━━━━━━━━━━━━━━━\n"
                                    "📊 <b>Texnik Tahlil</b> \u2014 Grafikdagi SMC strukturani (BOS, CHoCH, OB) AI yordamida matnli izohlab beradi.\n\n"
                                    "🌐 <b>Fundamental</b> \u2014 DXY, FED, global yangiliklar va makro drayverlarni tahlil qiladi.\n\n"
                                    "📈 <b>Hisobot</b> \u2014 So'nggi 50 ta signal statistikasini AI ko'zi bilan tahlil qilib, strategik tavsiya beradi.\n\n"
                                    "💬 <b>AI Chat</b> \u2014 Istalgan savol yoki chart rasmi yuboring \u2014 AI javob beradi.\n\n"
                                    "━━━━━━━━━━━━━━━━━━━━\n"
                                    "🔐 <b>Faqat Admin uchun:</b>\n"
                                    "⚡ <b>Scalping AI</b> \u2014 M5/M15 taymfreymlarda tezkor kirish rejasini beradi.\n"
                                    "⚖️ <b>Risk Status</b> \u2014 Hisob balansini ko'rsatadi.\n"
                                    "🚨 <b>PANIC CLOSE ALL</b> \u2014 Favqulodda vaziyatda barcha pozitsiyalarni yopadi.\n"
                                    "━━━━━━━━━━━━━━━━━━━━\n"
                                    "💡 <i>Istalgan vaqt rasm (chart) yuborib, AI tahlil so'rang!</i>"
                                )
                                await self.send(guide, cid=uid)

                            elif not m.get('text', '').startswith('/') or m.get('photo'):
                                # Erkin matn yoki rasm — hammaga ochiq
                                img_data = None
                                if m.get('photo'):
                                    fid = m['photo'][-1]['file_id']
                                    async with sess.get(f"{self.base}/getFile?file_id={fid}", proxy=self.proxy) as gr:
                                        if gr.status == 200:
                                            fpath = (await gr.json())['result']['file_path']
                                            async with sess.get(f"https://api.telegram.org/file/bot{self.cfg['bot_token']}/{fpath}", proxy=self.proxy) as dr:
                                                if dr.status == 200: img_data = await dr.read()

                                user_text = t or m.get('caption', '') or "Ushbu rasmni tahlil qiling."
                                with self.lock: bs['ai_requests'].append({
                                    'type': 'chat', 'symbol': 'KNOWLEDGE_BASE',
                                    'chat_id': uid, 'text': user_text, 'image': img_data
                                })
                                status_msg = "⏳ Rasm yuklanmoqda, AI tahlil qilmoqda..." if img_data else "⏳ AI tahlil boshlandi..."
                                await self.send(status_msg, cid=uid)
            except Exception as e:
                print(f"DEBUG: Poll Error: {e}")
                await asyncio.sleep(5)
