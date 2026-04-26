"""
tests/test_analytics.py
Analytics (trade report) modulini tekshirish.
"""
import pytest
from utils.analytics import generate_trade_report


class TestGenerateTradeReport:
    """generate_trade_report() funksiyasi uchun testlar"""

    def test_empty_signals_returns_default_message(self):
        """Signal yo'q bo'lsa standart xabar qaytadi."""
        state = {"signals_log": []}
        result = generate_trade_report(state)
        assert "hech qanday signal" in result.lower() or "nolda" in result

    def test_no_signals_key_returns_default(self):
        """signals_log kaliti bo'lmasa ham ishlaydi."""
        state = {}
        result = generate_trade_report(state)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_report_contains_win_loss_counts(self):
        """Hisobot W/L statistikasini o'z ichiga oladi."""
        state = {
            "signals_log": [
                {"symbol": "XAU/USD", "direction": "BUY", "entry": 2350.0, "outcome": "win"},
                {"symbol": "BTC/USDT", "direction": "SELL", "entry": 65000.0, "outcome": "loss"},
                {"symbol": "EUR/USD", "direction": "BUY", "entry": 1.1000, "outcome": "win"},
            ]
        }
        result = generate_trade_report(state)
        assert "3" in result        # Jami 3 ta
        assert "2" in result        # 2 ta win
        assert "1" in result        # 1 ta loss

    def test_report_shows_last_10_trades(self):
        """Hisobot oxirgi bitimlarni ko'rsatadi."""
        signals = [
            {"symbol": f"SYM{i}", "direction": "BUY", "entry": 100.0, "outcome": "win"}
            for i in range(20)
        ]
        state = {"signals_log": signals}
        result = generate_trade_report(state)
        # Oxirgi 10 ta signal ko'rsatilishi kerak
        assert "SYM19" in result  # eng so'nggisi

    def test_report_max_50_signals(self):
        """100 ta signal bo'lsa ham faqat so'nggi 50 tasi tahlil qilinadi."""
        signals = [
            {"symbol": "XAU/USD", "direction": "BUY", "entry": 100.0 + i, "outcome": "win"}
            for i in range(100)
        ]
        state = {"signals_log": signals}
        result = generate_trade_report(state)
        assert "50" in result  # Jami 50 ta signal

    def test_pending_signals_counted(self):
        """Natijasi yozilmagan (pending) signallar hisoblanadi."""
        state = {
            "signals_log": [
                {"symbol": "XAU/USD", "direction": "BUY", "entry": 2350.0},  # outcome yo'q = pending
                {"symbol": "BTC/USDT", "direction": "SELL", "entry": 65000.0, "outcome": "win"},
            ]
        }
        result = generate_trade_report(state)
        assert isinstance(result, str)
        assert "1" in result  # 1 ta pending

    def test_report_contains_symbol_names(self):
        """Hisobotda instrument nomlari ko'rinadi."""
        state = {
            "signals_log": [
                {"symbol": "XAU/USD", "direction": "BUY", "entry": 2350.0, "outcome": "win"},
            ]
        }
        result = generate_trade_report(state)
        assert "XAU/USD" in result
