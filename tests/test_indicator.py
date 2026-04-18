import pytest
import pandas as pd
import numpy as np
from core.indicator import GeminiIndicator

@pytest.fixture
def sample_config():
    return {
        'trend': {
            'ema_slow': 200, 'ema_fast': 50, 'atr_period': 14,
            'atr_mult_crypto': 1.5, 'atr_mult_forex': 2.5
        },
        'filters': {
            'min_volat_mult': 0.5, 'use_rsi': True, 'rsi_long_max': 62, 'rsi_short_min': 38
        },
        'smc': {
            'swing_len': 10, 'pivot_window': 30, 'ob_strength': 1.1, 'signal_mode': "Faqat BOS"
        },
        'tp': {'tp1_mult': 1.0, 'tp2_mult': 2.0, 'tp3_mult': 3.0, 'breakeven_tp': 1},
        'session': {'enabled': False}
    }

@pytest.fixture
def dummy_ohlcv():
    """Tayyor tahlil uchun sun'iy ma'lumotlar yaratish"""
    dates = pd.date_range("2024-01-01", periods=300, freq="15min", tz="UTC")
    df = pd.DataFrame({
        'open': np.linspace(100, 110, 300) + np.random.normal(0, 0.1, 300),
        'high': np.linspace(100, 110, 300) + 0.5 + np.random.normal(0, 0.1, 300),
        'low': np.linspace(100, 110, 300) - 0.5 + np.random.normal(0, 0.1, 300),
        'close': np.linspace(100, 110, 300) + np.random.normal(0, 0.1, 300),
        'volume': np.random.randint(100, 1000, 300)
    }, index=dates)
    return df

def test_compute_indicators(sample_config, dummy_ohlcv):
    indicator = GeminiIndicator(sample_config)
    df = indicator.compute_indicators(dummy_ohlcv, "BTC/USDT")
    
    assert 'ema200' in df.columns
    assert 'ema50' in df.columns
    assert 'atr' in df.columns
    assert 'rsi' in df.columns
    assert not df['ema200'].isnull().all()

def test_detect_structure(sample_config, dummy_ohlcv):
    indicator = GeminiIndicator(sample_config)
    df = indicator.compute_indicators(dummy_ohlcv, "BTC/USDT")
    df = indicator.find_pivots(df)
    df = indicator.detect_structure(df)
    
    assert 'bos_bull' in df.columns
    assert 'choch_bull' in df.columns

def test_detect_ob(sample_config, dummy_ohlcv):
    indicator = GeminiIndicator(sample_config)
    df = indicator.run_full(dummy_ohlcv, "BTC/USDT", "15m")
    
    assert 'is_bull_ob' in df.columns
    assert 'bull_confluence' in df.columns

def test_trade_state_transitions(sample_config):
    indicator = GeminiIndicator(sample_config)
    state = indicator.trade
    
    # Reset testi
    state.state = 1
    state.reset_trade()
    assert state.state == 0
    assert state.active == False
