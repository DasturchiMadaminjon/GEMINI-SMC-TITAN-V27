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
                            if d.startswith("ai_scalping") and uid not in self.admins:
                                await sess.post(f"{self.base}/answerCallbackQuery", proxy=self.proxy, json={'callback_query_id': cb['id'], 'text': "❌ Kirish adminlar uchun.", 'show_alert': True})
                                continue
                            
                            if d.startswith("ai_"):
                                t, s = d.replace("ai_","").split(":")
                                with self.lock: bs['ai_requests'].append({'type': t, 'symbol': s, 'chat_id': uid})
                                await self.send(f"⏳ <i>{s} uchun {t.upper()} tahlili tayyorlanmoqda...</i>", cid=uid)
                                # Callbackga har doim javob berish (Robust)
                                try: await sess.post(f"{self.base}/answerCallbackQuery", proxy=self.proxy, json={'callback_query_id': cb['id']})
                                except: pass

                        elif m:
                            t = m.get('text', '')
                            is_admin = uid in self.admins
                            ADMIN_KB = {'keyboard': [[{'text': "📊 Texnik Tahlil"}, {'text': "🌐 Fundamental"}],[{'text': "⚡ Scalping AI"}, {'text': "💬 AI Chat Assistant"}],[{'text': "⚖️ Risk Status"}, {'text': "📖 Qo'llanma"}],[{'text': "🚨 PANIC CLOSE ALL"}]], 'resize_keyboard': True}
                            USER_KB = {'keyboard': [[{'text': "📊 Texnik Tahlil"}, {'text': "🌐 Fundamental"}],[{'text': "💬 AI Chat Assistant"}, {'text': "📖 Qo'llanma"}]], 'resize_keyboard': True}
                            
                            if t == "/start":
                                kb = ADMIN_KB if is_admin else USER_KB
                                await sess.post(f"{self.base}/sendMessage", proxy=self.proxy, json={'chat_id': uid, 'text': "<b>V27.2 A+ TITAN MASTER</b>", 'reply_markup': kb, 'parse_mode': 'HTML'})
                            elif any(x in t for x in ["Tahlil", "Fundamental", "Scalping"]):
                                if "Scalp" in t and not is_admin:
                                    await self.send("❌ Faqat Admin uchun.", cid=uid)
                                    continue
                                type_ai = 'fundamental' if 'Fund' in t else ('scalping' if 'Scalp' in t else 'technical')
                                ikb = {'inline_keyboard': [[{'text': s, 'callback_data': f"ai_{type_ai}:{s}"}] for s in sym_list]}
                                await self.send("🔍 Instrumentni tanlang:", cid=uid, kb=json.dumps(ikb))
                            elif any(x in t.upper() for x in ["PANIC", "RISK", "STATUS"]):
                                if is_admin:
                                    if "PANIC" in t.upper():
                                        await self.send("🚨 <b>EMERGENCY CALLED!</b>", cid=uid)
                                        with self.lock: bs['panic_request'] = True
                                    else:
                                        with self.lock: b = bs['terminal']['balance']
                                        await self.send(f"⚖️ <b>Balance: ${b}</b>", cid=uid)
                            elif any(x in t for x in ["Qo'llanma", "Yo'riqnoma", "Manual"]):
                                await self.send("📖 Yo'riqnoma: Tugmani bosing, instrumentni tanlang va kuting.", cid=uid)
                            elif any(x in t for x in ["Chat Assistant", "💬 AI Chat"]):
                                await self.send("💬 Savol yoki rasm (chart) yuboring.", cid=uid)
                            elif not m.get('text', '').startswith('/') or m.get('photo'):
                                # Chat Assistant — matn yoki rasm (bo'sh text ham qabul qilinadi)
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
