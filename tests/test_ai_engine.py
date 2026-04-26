"""
tests/test_ai_engine.py
AIEngine klassini unittest va mock yordamida tekshirish.
"""
import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from utils.ai_engine import AIEngine


class TestAIEngineInit:
    """AIEngine initsializatsiya testlari"""

    def test_init_with_string_keys(self):
        """Vergul bilan ajratilgan string kalitlar to'g'ri parse qilinadi."""
        keys = "AIzaSyKey1xxxxxxxxxxxxxxxxxxxx,AIzaSyKey2xxxxxxxxxxxxxxxxxxxx"
        engine = AIEngine(api_keys=keys)
        assert len(engine.api_keys) == 2

    def test_init_with_list_keys(self):
        """List formatidagi kalitlar to'g'ri yuklandi."""
        keys = ["AIzaSyKey1xxxxxxxxxxxxxxxxxxxx", "AIzaSyKey2xxxxxxxxxxxxxxxxxxxx"]
        engine = AIEngine(api_keys=keys)
        assert len(engine.api_keys) == 2

    def test_init_with_empty_keys(self):
        """Bo'sh kalitlarda model None bo'ladi."""
        engine = AIEngine(api_keys=[])
        assert engine.model is None

    def test_init_filters_short_keys(self):
        """Juda qisqa (20 harfdan kam) kalitlar o'tkazib yuboriladi."""
        engine = AIEngine(api_keys=["short", "AIzaSyValidKeyxxxxxxxxxxxxxxxx"])
        assert len(engine.api_keys) == 1

    def test_rotate_key(self):
        """Key rotatsiyasi indeksni o'zgartiradi."""
        keys = ["AIzaSyKey1xxxxxxxxxxxxxxxxxxxx", "AIzaSyKey2xxxxxxxxxxxxxxxxxxxx"]
        engine = AIEngine.__new__(AIEngine)
        engine.api_keys = keys
        engine.current_key_index = 0
        engine.model_name = "gemini-1.5-flash"
        engine.model = MagicMock()

        with patch("google.generativeai.configure"), \
             patch("google.generativeai.GenerativeModel", return_value=MagicMock()):
            result = engine._rotate_key()

        assert result is True
        assert engine.current_key_index == 1

    def test_rotate_key_single_key(self):
        """Faqat bitta kalit bo'lsa rotatsiya False qaytaradi."""
        engine = AIEngine.__new__(AIEngine)
        engine.api_keys = ["AIzaSyKey1xxxxxxxxxxxxxxxxxxxx"]
        engine.current_key_index = 0
        result = engine._rotate_key()
        assert result is False


class TestAIEngineAnalysis:
    """get_analysis() metodi uchun testlar (mock bilan)"""

    def _make_engine(self, keys=None):
        """Mock engine yaratish yordamchisi"""
        engine = AIEngine.__new__(AIEngine)
        engine.api_keys = keys or ["AIzaSyKey1xxxxxxxxxxxxxxxxxxxx"]
        engine.current_key_index = 0
        engine.model_name = "gemini-1.5-flash"
        engine.personas = {
            "technical": "SMC Titan persona...",
            "scalping": "Scalp Master persona...",
            "fundamental": "Macro Analyst persona...",
            "chat": "SMC Mentor persona...",
            "analytics": "Hedge Fund persona..."
        }
        engine.drafts = {
            "technical": "⚠️ DRAFT MODE: BOS/CHoCH...",
            "scalping": "⚠️ SCALP DRAFT...",
            "fundamental": "⚠️ MACRO DRAFT...",
            "chat": "⚠️ MENTOR DRAFT: AI band."
        }
        return engine

    def _run(self, coro):
        """Async funksiyani sinxron ishlatish yordamchisi"""
        return asyncio.run(coro)

    def test_no_model_returns_error(self):
        """Model bo'lmasa xato xabari qaytadi."""
        engine = self._make_engine(keys=[])
        engine.model = None
        result = self._run(engine.get_analysis("test prompt", "technical"))
        assert "API kalitlari sozlanmagan" in result or "❌" in result

    def test_successful_analysis(self):
        """Muvaffaqiyatli AI javobi qaytadi."""
        engine = self._make_engine()
        mock_response = MagicMock()
        mock_response.text = "📊 SMC Tahlil: Bullish BOS aniqlandi..."
        mock_model = MagicMock()
        mock_model.generate_content.return_value = mock_response
        engine.model = mock_model
        result = self._run(engine.get_analysis("XAU/USD tahlil", "technical"))
        assert "SMC Tahlil" in result

    def test_rate_limit_returns_draft(self):
        """429 xatosida DRAFT MODE qaytadi."""
        engine = self._make_engine()
        mock_model = MagicMock()
        mock_model.generate_content.side_effect = Exception("429 Too Many Requests")
        engine.model = mock_model
        result = self._run(engine.get_analysis("test", "technical"))
        assert "DRAFT" in result or "⚠️" in result

    def test_expired_key_returns_error(self):
        """400/expired xatosida ma'lumotli xabar qaytadi."""
        engine = self._make_engine()
        mock_model = MagicMock()
        mock_model.generate_content.side_effect = Exception("400 API key expired")
        engine.model = mock_model
        result = self._run(engine.get_analysis("test", "technical"))
        assert "❌" in result

    def test_persona_types_exist(self):
        """Barcha persona turlari mavjud."""
        engine = self._make_engine()
        engine.model = None
        for ptype in ["technical", "scalping", "fundamental", "chat", "analytics"]:
            assert ptype in engine.personas
