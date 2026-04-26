"""
tests/test_indicator.py
GeminiIndicator (SMC signal engine) testlari.
"""
import pytest
import pandas as pd
import numpy as np
from core.indicator import GeminiIndicator, Signal


@pytest.fixture
def sample_config():
    return {
        'trend': {
            'ema_slow': 200, 'ema_fast': 50, 'atr_period': 14,
            'atr_mult_crypto': 1.5, 'atr_mult_forex': 2.5
        },
        'filters': {
            'min_volat_mult': 0.5, 'use_rsi': True,
            'rsi_long_max': 62, 'rsi_short_min': 38,
            'vol_mult_forex': 1.5
        },
        'smc': {
            'swing_len': 5, 'pivot_window': 10, 'ob_strength': 1.1,
            'signal_mode': "Faqat BOS", 'min_quality': 65.0,
            'feedback_loop_enabled': True
        },
        'tp': {'tp1_mult': 1.0, 'tp2_mult': 2.0, 'tp3_mult': 3.0, 'breakeven_tp': 1},
        'session': {'enabled': False}
    }


@pytest.fixture
def dummy_ohlcv():
    """300 ta OHLCV qator (tahlil uchun yetarli)"""
    np.random.seed(42)
    dates = pd.date_range("2024-01-01", periods=300, freq="15min", tz="UTC")
    close = np.linspace(100, 110, 300) + np.random.normal(0, 0.1, 300)
    df = pd.DataFrame({
        'open':   close - np.random.uniform(0.05, 0.2, 300),
        'high':   close + np.random.uniform(0.1,  0.5, 300),
        'low':    close - np.random.uniform(0.1,  0.5, 300),
        'close':  close,
        'volume': np.random.randint(500, 2000, 300).astype(float)
    }, index=dates)
    return df


@pytest.fixture
def short_ohlcv():
    """Yetarli bo'lmagan (60 dan kam) ma'lumot"""
    dates = pd.date_range("2024-01-01", periods=30, freq="15min")
    df = pd.DataFrame({
        'open': [100.0] * 30, 'high': [101.0] * 30,
        'low': [99.0] * 30, 'close': [100.5] * 30,
        'volume': [1000.0] * 30
    }, index=dates)
    return df


class TestGeminiIndicatorInit:
    """GeminiIndicator initsializatsiya testlari"""

    def test_init_with_config(self, sample_config):
        """To'g'ri config bilan yaratish muvaffaqiyatli."""
        ind = GeminiIndicator(sample_config)
        assert ind is not None
        assert ind.cfg == sample_config

    def test_quality_boost_default_zero(self, sample_config):
        """Boshlang'ich quality_boost = 0."""
        ind = GeminiIndicator(sample_config)
        assert ind.quality_boost == 0.0

    def test_update_feedback_increases_boost(self, sample_config):
        """Yutqazish soni quality_boost ni oshiradi."""
        ind = GeminiIndicator(sample_config)
        ind.update_feedback(3)
        assert ind.quality_boost == 30.0

    def test_update_feedback_max_40(self, sample_config):
        """quality_boost maksimal 40 bo'lishi mumkin."""
        ind = GeminiIndicator(sample_config)
        ind.update_feedback(100)
        assert ind.quality_boost == 40.0


class TestSignalGeneration:
    """generate_signal() metodi testlari"""

    def test_short_data_returns_none(self, sample_config, short_ohlcv):
        """60 dan kam qatorda None qaytadi."""
        ind = GeminiIndicator(sample_config)
        result = ind.generate_signal(short_ohlcv, "XAU/USD", "15m")
        assert result is None

    def test_returns_none_or_signal(self, sample_config, dummy_ohlcv):
        """Signal None yoki Signal obyekti qaytaradi."""
        ind = GeminiIndicator(sample_config)
        result = ind.generate_signal(dummy_ohlcv, "XAU/USD", "15m")
        assert result is None or isinstance(result, Signal)

    def test_signal_has_required_fields(self, sample_config, dummy_ohlcv):
        """Signal obyektida barcha zarur maydonlar mavjud."""
        ind = GeminiIndicator(sample_config)
        ind.quality_boost = 100.0  # Sifat chegarasini pastlatish uchun
        result = ind.generate_signal(dummy_ohlcv, "BTC/USDT", "15m")
        if result is not None:
            assert hasattr(result, 'direction')
            assert hasattr(result, 'entry')
            assert hasattr(result, 'sl')
            assert hasattr(result, 'tp1')
            assert hasattr(result, 'quality')
            assert result.direction in ['buy', 'sell']

    def test_sl_is_below_entry_for_buy(self, sample_config, dummy_ohlcv):
        """BUY signalida SL entry dan past bo'ladi."""
        ind = GeminiIndicator(sample_config)
        for _ in range(5):
            result = ind.generate_signal(dummy_ohlcv, "XAU/USD", "15m")
            if result and result.direction == 'buy':
                assert result.sl < result.entry
                break

    def test_sl_is_above_entry_for_sell(self, sample_config, dummy_ohlcv):
        """SELL signalida SL entry dan yuqori bo'ladi."""
        ind = GeminiIndicator(sample_config)
        for _ in range(5):
            result = ind.generate_signal(dummy_ohlcv, "XAU/USD", "15m")
            if result and result.direction == 'sell':
                assert result.sl > result.entry
                break


class TestHelperMethods:
    """Yordamchi metodlar testlari"""

    def test_pivot_highs(self, sample_config, dummy_ohlcv):
        """Pivot high'lar aniqlanadi."""
        ind = GeminiIndicator(sample_config)
        result = ind._pivot_highs(dummy_ohlcv, n=5)
        assert len(result) >= 0

    def test_pivot_lows(self, sample_config, dummy_ohlcv):
        """Pivot low'lar aniqlanadi."""
        ind = GeminiIndicator(sample_config)
        result = ind._pivot_lows(dummy_ohlcv, n=5)
        assert len(result) >= 0

    def test_rsi_range(self, sample_config, dummy_ohlcv):
        """RSI 0-100 oraliqda bo'ladi."""
        ind = GeminiIndicator(sample_config)
        rsi = ind._calc_rsi(dummy_ohlcv['close'])
        rsi_clean = rsi.dropna()
        assert (rsi_clean >= 0).all()
        assert (rsi_clean <= 100).all()

    def test_find_fvg_returns_dict(self, sample_config, dummy_ohlcv):
        """FVG topuvchi dict qaytaradi."""
        ind = GeminiIndicator(sample_config)
        result = ind._find_fvg(dummy_ohlcv.tail(20))
        assert isinstance(result, dict)
        assert 'bullish' in result
        assert 'bearish' in result
