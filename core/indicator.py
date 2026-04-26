import pandas as pd
import numpy as np
from dataclasses import dataclass

@dataclass
class Signal:
    direction: str
    symbol: str
    entry: float
    sl: float
    tp1: float
    tp2: float
    tp3: float
    quality: float
    reason: str
    timestamp: pd.Timestamp


class GeminiIndicator:
    def __init__(self, config):
        self.cfg = config
        self.smc = config.get('smc', {})
        self.tp  = config.get('tp',  {})
        self.flt = config.get('filters', {})
        self.quality_boost = 0.0

    def update_feedback(self, loss_count: int):
        """Yutqazish ketma-ketligi bo'yicha sifat bandini avtomatik ko'tarish."""
        if self.smc.get('feedback_loop_enabled', True):
            self.quality_boost = min(loss_count * 10.0, 40.0)

    # ------------------------------------------------------------------
    # YORDAMCHI HISOB-KITOB METODLARI
    # ------------------------------------------------------------------

    @staticmethod
    def _pivot_highs(df: pd.DataFrame, n: int = 5) -> pd.Series:
        h = df['high']
        return h[(h == h.rolling(2*n+1, center=True).max())]

    @staticmethod
    def _pivot_lows(df: pd.DataFrame, n: int = 5) -> pd.Series:
        l = df['low']
        return l[(l == l.rolling(2*n+1, center=True).min())]

    @staticmethod
    def _calc_rsi(series: pd.Series, period: int = 14) -> pd.Series:
        delta = series.diff()
        gain = delta.clip(lower=0).rolling(period).mean()
        loss = (-delta.clip(upper=0)).rolling(period).mean()
        rs = gain / loss.replace(0, np.nan)
        return 100 - (100 / (1 + rs))

    @staticmethod
    def _find_fvg(df: pd.DataFrame) -> dict:
        """
        Fair Value Gap (Imbalance) aniqlash.
        Bullish FVG: candle[i-2].high < candle[i].low
        Bearish FVG: candle[i-2].low  > candle[i].high
        """
        result = {'bullish': [], 'bearish': []}
        for i in range(2, len(df)):
            lo = df['low'].iat[i]
            hi = df['high'].iat[i]
            prev2_hi = df['high'].iat[i-2]
            prev2_lo = df['low'].iat[i-2]
            if prev2_hi < lo:
                result['bullish'].append((prev2_hi, lo))
            if prev2_lo > hi:
                result['bearish'].append((hi, prev2_lo))
        return result

    # ------------------------------------------------------------------
    # ASOSIY SIGNAL GENERATORI
    # ------------------------------------------------------------------

    def generate_signal(self, df: pd.DataFrame, symbol: str,
                         tf: str, loss_streak: int = 0):
        if len(df) < 60:
            return None

        self.update_feedback(loss_streak)
        df = df.copy().reset_index(drop=True)

        # --- Indikatorlar ---
        n = self.smc.get('swing_len', 5)
        df['ema200'] = df['close'].rolling(200).mean()
        df['ema50']  = df['close'].rolling(50).mean()
        df['rsi']    = self._calc_rsi(df['close'])
        df['vol_ma'] = df['volume'].rolling(20).mean()

        last = df.iloc[-1]
        prev = df.iloc[-2]
        close = last['close']

        # Sifat boshi
        quality = 50.0

        # 1. EMA Trend (+15)
        bullish_trend = close > last['ema200'] and close > last['ema50']
        bearish_trend = close < last['ema200'] and close < last['ema50']
        if bullish_trend or bearish_trend:
            quality += 15

        # 2. RSI filtri (+10)
        rsi = last['rsi']
        rsi_ok_bull = 40 <= rsi <= 65
        rsi_ok_bear = 35 <= rsi <= 60
        if rsi_ok_bull or rsi_ok_bear:
            quality += 10

        # 3. Hajm tasdig'i (+10)
        if last['volume'] > last['vol_ma'] * self.flt.get('vol_mult_forex', 1.5):
            quality += 10

        # 4. Sham kuchi (+5)
        body = abs(close - last['open'])
        prev_body = abs(prev['close'] - prev['open'])
        if body > prev_body * 1.3:
            quality += 5

        # 5. BOS (Break of Structure) tekshiruvi (+15)
        ph = self._pivot_highs(df, n)
        pl = self._pivot_lows(df, n)
        bos_bull = len(ph) >= 2 and close > ph.iloc[-1]   # Yuqori High yangi max
        bos_bear = len(pl) >= 2 and close < pl.iloc[-1]   # Pastki Low yangi min
        if bos_bull or bos_bear:
            quality += 15

        # 6. FVG mavjudligi (+5 bonus)
        fvg = self._find_fvg(df.tail(20))
        has_bull_fvg = len(fvg['bullish']) > 0
        has_bear_fvg = len(fvg['bearish']) > 0
        if (bullish_trend and has_bull_fvg) or (bearish_trend and has_bear_fvg):
            quality += 5

        # 7. FIBONACCI Golden Pocket (0.618-0.786) tekshiruvi (+10)
        fib_in_zone = False
        swing_high = df['high'].rolling(30).max().iloc[-1]
        swing_low  = df['low'].rolling(30).min().iloc[-1]
        fib_range  = swing_high - swing_low
        if fib_range > 0:
            fib_618 = swing_high - fib_range * 0.618
            fib_786 = swing_high - fib_range * 0.786
            fib_50  = swing_high - fib_range * 0.500
            # Bullish: narx Discount zonada (0.618-0.786)
            if bullish_trend and fib_786 <= close <= fib_618:
                quality += 10
                fib_in_zone = True
            # Bearish: narx Premium zonada (0.214-0.382)
            fib_214 = swing_high - fib_range * 0.214
            fib_382 = swing_high - fib_range * 0.382
            if bearish_trend and fib_382 <= close <= fib_214:
                quality += 10
                fib_in_zone = True

        threshold = float(self.smc.get('min_quality', 65.0)) + self.quality_boost
        if quality < threshold:
            return None

        # --- RR uchun SL va TP hisoblash (ATR bazasida) ---
        atr = (df['high'] - df['low']).rolling(14).mean().iloc[-1]
        atr = max(atr, close * 0.001)   # Minimal ATR

        tp1m = float(self.tp.get('tp1_mult', 1.0))
        tp2m = float(self.tp.get('tp2_mult', 2.0))
        tp3m = float(self.tp.get('tp3_mult', 3.5))

        # --- BUY signali ---
        if bullish_trend and bos_bull and rsi_ok_bull:
            sl  = close - atr * 1.5
            tp1 = close + atr * tp1m
            tp2 = close + atr * tp2m
            tp3 = close + atr * tp3m
            reason = "SMC BOS↑"
            if has_bull_fvg: reason += " + FVG"
            if fib_in_zone:  reason += " + Fibo 0.618"
            return Signal('buy', symbol, close, sl, tp1, tp2, tp3,
                          round(quality, 1), reason, df.index[-1] if hasattr(df.index[-1], 'strftime') else pd.Timestamp.now())

        # --- SELL signali ---
        if bearish_trend and bos_bear and rsi_ok_bear:
            sl  = close + atr * 1.5
            tp1 = close - atr * tp1m
            tp2 = close - atr * tp2m
            tp3 = close - atr * tp3m
            reason = "SMC BOS↓"
            if has_bear_fvg: reason += " + FVG"
            if fib_in_zone:  reason += " + Fibo 0.786"
            return Signal('sell', symbol, close, sl, tp1, tp2, tp3,
                          round(quality, 1), reason, df.index[-1] if hasattr(df.index[-1], 'strftime') else pd.Timestamp.now())

        return None
