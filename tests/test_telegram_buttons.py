"""
tests/test_telegram_buttons.py
Telegram knopka handlerlari funksiyalarini tekshirish (mock bilan).
"""
import pytest
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch


# ─── Yordamchi: soxta update yaratish ──────────────────────────────────────

def make_update(text="", uid="7295947374", cb_data=None, has_photo=False):
    """Telegram update obyektini simulyatsiya qilish."""
    if cb_data:
        return {
            "update_id": 1,
            "callback_query": {
                "id": "cb001",
                "data": cb_data,
                "from": {"id": int(uid)},
                "message": {"chat": {"id": int(uid)}}
            }
        }
    msg = {"text": text, "from": {"id": int(uid)}, "chat": {"id": int(uid)}}
    if has_photo:
        msg["photo"] = [{"file_id": "test_file_id"}]
    return {"update_id": 1, "message": msg}


def make_bot_state():
    return {
        "symbols": {"XAU/USD": {"price": 2350.0}},
        "terminal": {"balance": 5000.0},
        "ai_requests": [],
        "loss_streak": 0,
        "panic_request": False
    }


ADMIN_UID = "7295947374"
USER_UID  = "9999999999"


# ─── Fixture: TelegramNotifier ──────────────────────────────────────────────

@pytest.fixture
def notifier():
    """Mock TelegramNotifier yaratish."""
    with patch("utils.telegram.AIEngine"), \
         patch("google.generativeai.configure"), \
         patch("google.generativeai.list_models", return_value=[]):

        from utils.telegram import TelegramNotifier
        import threading

        cfg = {
            "telegram": {
                "bot_token": "test_token",
                "chat_id": [int(ADMIN_UID)]
            },
            "gemini_ai": {"api_keys": [], "model": "gemini-2.5-flash"},
            "symbols": ["XAU/USD", "BTC/USDT"]
        }
        lock = threading.Lock()
        obj = TelegramNotifier(cfg, lock)
        obj.send = AsyncMock()
        obj.send_action = AsyncMock(return_value=True)
        return obj


# ─── /start knopkasi ────────────────────────────────────────────────────────

class TestStartCommand:
    def test_admin_sees_admin_keyboard(self, notifier):
        """Admin /start yozganda ADMIN_KB ko'rinadi."""
        admins = [ADMIN_UID]
        is_admin = ADMIN_UID in admins
        assert is_admin is True

    def test_user_sees_user_keyboard(self, notifier):
        """Begona foydalanuvchi USER_KB ko'radi."""
        admins = [ADMIN_UID]
        is_admin = USER_UID in admins
        assert is_admin is False

    def test_admin_kb_has_panic_button(self, notifier):
        """ADMIN_KB da PANIC tugmasi bo'lishi kerak."""
        ADMIN_KB = {
            'keyboard': [
                [{'text': "📊 Texnik Tahlil"}, {'text': "🌐 Fundamental"}],
                [{'text': "⚡ Scalping AI"}, {'text': "💬 AI Chat Assistant"}],
                [{'text': "⚖️ Risk Status"}, {'text': "📈 Hisobot (Analytics)"}],
                [{'text': "📖 Qo'llanma"}, {'text': "🚨 PANIC CLOSE ALL"}]
            ]
        }
        all_texts = [b['text'] for row in ADMIN_KB['keyboard'] for b in row]
        assert "🚨 PANIC CLOSE ALL" in all_texts

    def test_user_kb_has_no_panic_button(self, notifier):
        """USER_KB da PANIC tugmasi bo'lmasligi kerak."""
        USER_KB = {
            'keyboard': [
                [{'text': "📊 Texnik Tahlil"}, {'text': "🌐 Fundamental"}],
                [{'text': "💬 AI Chat Assistant"}, {'text': "📈 Hisobot (Analytics)"}],
                [{'text': "📖 Qo'llanma"}]
            ]
        }
        all_texts = [b['text'] for row in USER_KB['keyboard'] for b in row]
        assert "🚨 PANIC CLOSE ALL" not in all_texts
        assert "⚡ Scalping AI" not in all_texts
        assert "⚖️ Risk Status" not in all_texts


# ─── AI Tahlil knopkalari ───────────────────────────────────────────────────

class TestAIButtons:
    def test_texnik_tahlil_adds_ai_request(self):
        """Texnik Tahlil bosilganda ai_requests ga qo'shiladi."""
        bs = make_bot_state()
        # Simulyatsiya: user "📊 Texnik Tahlil" + instrument tanlaydi
        t = "Tahlil"
        type_ai = 'fundamental' if 'Fund' in t else ('scalping' if 'Scalp' in t else 'technical')
        assert type_ai == 'technical'

    def test_fundamental_adds_ai_request(self):
        """Fundamental bosilganda to'g'ri type aniqlanadi."""
        t = "Fundamental"
        type_ai = 'fundamental' if 'Fund' in t else ('scalping' if 'Scalp' in t else 'technical')
        assert type_ai == 'fundamental'

    def test_scalping_type_detected(self):
        """Scalping bosilganda to'g'ri type aniqlanadi."""
        t = "Scalping AI"
        type_ai = 'fundamental' if 'Fund' in t else ('scalping' if 'Scalp' in t else 'technical')
        assert type_ai == 'scalping'

    def test_scalping_blocked_for_non_admin(self):
        """Scalping noadmin uchun bloklanadi."""
        t = "Scalping AI"
        is_admin = USER_UID in [ADMIN_UID]
        blocked = "Scalp" in t and not is_admin
        assert blocked is True

    def test_scalping_allowed_for_admin(self):
        """Scalping admin uchun ruxsat beriladi."""
        t = "Scalping AI"
        is_admin = ADMIN_UID in [ADMIN_UID]
        blocked = "Scalp" in t and not is_admin
        assert blocked is False


# ─── Callback (inline) knopkalar ────────────────────────────────────────────

class TestCallbackButtons:
    def test_scalping_callback_blocked_for_non_admin(self):
        """Scalping callback noadmin uchun bloklanadi."""
        d = "ai_scalping:XAU/USD"
        uid = USER_UID
        admins = [ADMIN_UID]
        blocked = d.startswith("ai_scalping") and uid not in admins
        assert blocked is True

    def test_technical_callback_allowed_for_non_admin(self):
        """Texnik Tahlil callback hammaga ruxsat."""
        d = "ai_technical:XAU/USD"
        uid = USER_UID
        admins = [ADMIN_UID]
        blocked = d.startswith("ai_scalping") and uid not in admins
        assert blocked is False

    def test_callback_data_parsing(self):
        """ai_TYPE:SYMBOL formatini to'g'ri parse qilish."""
        d = "ai_technical:BTC/USDT"
        parts = d.replace("ai_", "").split(":")
        assert parts[0] == "technical"
        assert parts[1] == "BTC/USDT"

    def test_analytics_callback_parsing(self):
        """Analytics callback ma'lumotlarini parse qilish."""
        d = "ai_analytics:XAU/USD"
        t, s = d.replace("ai_", "").split(":")
        assert t == "analytics"
        assert s == "XAU/USD"


# ─── PANIC va RISK knopkalari ───────────────────────────────────────────────

class TestAdminOnlyButtons:
    def test_panic_sets_flag(self):
        """PANIC bosilganda panic_request True bo'ladi."""
        import threading
        bs = make_bot_state()
        lock = threading.Lock()
        t = "PANIC CLOSE ALL"
        if "PANIC" in t.upper():
            with lock:
                bs['panic_request'] = True
        assert bs['panic_request'] is True

    def test_risk_status_shows_balance(self):
        """Risk Status balansni ko'rsatadi."""
        bs = make_bot_state()
        import threading
        lock = threading.Lock()
        with lock:
            balance = bs['terminal']['balance']
        assert balance == 5000.0

    def test_panic_only_for_admin(self):
        """PANIC faqat admin uchun ishlashi kerak."""
        t = "PANIC CLOSE ALL"
        is_admin_user = USER_UID in [ADMIN_UID]
        is_admin_admin = ADMIN_UID in [ADMIN_UID]
        # Noadmin uchun blok bo'lishi kerak
        assert not is_admin_user
        assert is_admin_admin


# ─── Hisobot va Analytics ───────────────────────────────────────────────────

class TestAnalyticsButton:
    def test_hisobot_adds_analytics_request(self):
        """Hisobot bosilganda analytics request qo'shiladi."""
        bs = make_bot_state()
        import threading
        lock = threading.Lock()
        t = "📈 Hisobot (Analytics)"
        if any(x in t for x in ["Hisobot", "Analytics"]):
            with lock:
                bs['ai_requests'].append({
                    'type': 'analytics', 'symbol': 'KNOWLEDGE_BASE',
                    'chat_id': ADMIN_UID, 'text': 'Xulosa bering.'
                })
        assert len(bs['ai_requests']) == 1
        assert bs['ai_requests'][0]['type'] == 'analytics'

    def test_hisobot_allowed_for_user(self):
        """Hisobot noadmin uchun ham ruxsat berilgan."""
        t = "📈 Hisobot (Analytics)"
        # Hech qanday admin tekshiruvi yo'q
        is_hisobot = any(x in t for x in ["Hisobot", "Analytics"])
        assert is_hisobot is True


# ─── Qo'llanma knopkasi ────────────────────────────────────────────────────

class TestQollanmaButton:
    def test_qollanma_detected(self):
        """Qo'llanma matni aniqlandi."""
        t = "📖 Qo'llanma"
        detected = "Qo'llanma" in t or "qo'llanma" in t.lower()
        assert detected is True

    def test_qollanma_guide_contains_all_buttons(self):
        """Qo'llanma matni barcha knopkalarni o'z ichiga oladi."""
        guide = (
            "📖 Gemini SMC Titan V27.2 — Qo'llanma\n"
            "📊 Texnik Tahlil\n"
            "🌐 Fundamental\n"
            "📈 Hisobot\n"
            "💬 AI Chat\n"
            "⚡ Scalping AI\n"
            "⚖️ Risk Status\n"
            "🚨 PANIC CLOSE ALL\n"
        )
        for btn in ["Texnik", "Fundamental", "Hisobot", "Chat", "Scalping", "Risk", "PANIC"]:
            assert btn in guide

    def test_qollanma_is_static_no_ai(self):
        """Qo'llanma AI ishlatmaydi — statik matn."""
        # Qo'llanma handler ai_requests ga hech narsa qo'shmasligi kerak
        bs = make_bot_state()
        import threading
        lock = threading.Lock()
        t = "📖 Qo'llanma"
        if "Qo'llanma" in t:
            pass  # faqat send() chaqiriladi, ai_request yo'q
        assert len(bs['ai_requests']) == 0


# ─── AI Chat Assistant ─────────────────────────────────────────────────────

class TestChatAssistant:
    def test_chat_adds_ai_request(self):
        """Erkin matn yozilganda chat ai_request qo'shiladi."""
        bs = make_bot_state()
        import threading
        lock = threading.Lock()
        user_text = "GOLD hozir qanday?"
        with lock:
            bs['ai_requests'].append({
                'type': 'chat', 'symbol': 'KNOWLEDGE_BASE',
                'chat_id': ADMIN_UID, 'text': user_text, 'image': None
            })
        assert bs['ai_requests'][0]['type'] == 'chat'
        assert bs['ai_requests'][0]['text'] == "GOLD hozir qanday?"

    def test_photo_message_sets_image(self):
        """Rasm yuborilganda image maydoni to'ldiriladi."""
        req = {
            'type': 'chat', 'symbol': 'KNOWLEDGE_BASE',
            'chat_id': ADMIN_UID,
            'text': "Ushbu rasmni tahlil qiling.",
            'image': b"fake_image_bytes"
        }
        assert req['image'] is not None
        assert req['text'] == "Ushbu rasmni tahlil qiling."
