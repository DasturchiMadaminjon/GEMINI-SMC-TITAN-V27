import ccxt
import time
import pandas as pd
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
try:
    from .tradingview import TradingViewClient
    TV_AVAILABLE = True
except (ImportError, ModuleNotFoundError):
    TV_AVAILABLE = False
    logger.warning("utils/tradingview.py topilmadi. TradingView zaxira manbasi o'chirildi.")

logger = logging.getLogger(__name__)

try:
    import yfinance as yf
    YF_AVAILABLE = True
except ImportError:
    YF_AVAILABLE = False
    logger.warning("yfinance topilmadi. pip install yfinance")

EXCHANGES = {
    'binance': 'binance',
    'bybit':   'bybit',
    'okx':     'okx',
    'kraken':  'kraken',
    'kucoin':  'kucoin',
    'bitget':  'bitget',
    'mexc':    'mexc',
    'gate':    'gate',
    'uznex':   'uznex',
}

# Bot symbol → Yahoo Finance ticker
YF_SYMBOL_MAP = {
    # GOLD va metallar
    'XAU/USD':  'GC=F',
    'XAUUSD':   'GC=F',
    'GOLD':     'GC=F',
    'XAG/USD':  'SI=F',
    'XAGUSD':   'SI=F',
    'SILVER':   'SI=F',

    # Forex
    'EUR/USD':  'EURUSD=X',
    'GBP/USD':  'GBPUSD=X',
    'USD/JPY':  'USDJPY=X',
    'USD/CHF':  'USDCHF=X',
    'AUD/USD':  'AUDUSD=X',
    'USD/CAD':  'USDCAD=X',
    'NZD/USD':  'NZDUSD=X',

    # Kripto
    'BTC/USDT': 'BTC-USD',
    'ETH/USDT': 'ETH-USD',
    'SOL/USDT': 'SOL-USD',
    'XRP/USDT': 'XRP-USD',
    'BNB/USDT': 'BNB-USD',
    'ADA/USDT': 'ADA-USD',
    'DOGE/USDT':'DOGE-USD',
    'AVAX/USDT':'AVAX-USD',
    'DOT/USDT': 'DOT-USD',
    'MATIC/USDT':'MATIC-USD',
}

# Bot timeframe → yfinance interval
YF_INTERVAL_MAP = {
    '1m': '1m',  '3m': '1m',  '5m': '5m',
    '15m':'15m', '30m':'30m', '45m':'30m',
    '1h': '1h',  '2h': '1h',  '3h': '1h',
    '4h': '1h',  '1d': '1d',  '1w': '1wk',
}

# yfinance interval → ma'lumot olinadigan davr (period)
YF_PERIOD_MAP = {
    '1m':  '7d',
    '5m':  '60d',
    '15m': '60d',
    '30m': '60d',
    '1h':  '730d',
    '1d':  'max',
    '1wk': 'max',
}


class ExchangeClient:
    def __init__(self, config: dict):
        cfg  = config['exchange']
        name = cfg['name'].lower()
        self.name   = name
        self.config = config
        self.exchange = None
        self.tv = TradingViewClient() if TV_AVAILABLE else None
        self._ticker_cache = {}

        if name == 'tradingview' or name == 'yahoo':
            if not YF_AVAILABLE:
                logger.error("yfinance o'rnatilmagan: pip install yfinance")
            else:
                logger.info(f"Ma'lumot manbai: {name.upper()} (Backup tizimi faol)")
            return

        # ccxt rejimi (explicit binance/bybit/okx/... belgilanganda)
        if name not in EXCHANGES:
            raise ValueError(
                f"Noma'lum manba: {name}. "
                f"Mavjud: {list(EXCHANGES.keys()) + ['tradingview', 'yahoo']}"
            )

        api_key    = cfg.get('api_key', '')
        api_secret = cfg.get('api_secret', '')
        if api_key    in ('YOUR_API_KEY', ''): api_key    = ''
        if api_secret in ('YOUR_SECRET',  ''): api_secret = ''

        params = {
            'apiKey':          api_key,
            'secret':          api_secret,
            'enableRateLimit': True,
        }
        if api_key == '' and cfg.get('testnet', False):
            cfg['testnet'] = False
            logger.info("API kalitsiz, testnet o'chirildi")

        if cfg.get('testnet', False):
            params['options'] = {'defaultType': 'future'}
            if name == 'binance':
                params['urls'] = {'api': {'rest': 'https://testnet.binancefuture.com'}}
            elif name == 'bybit':
                params['testnet'] = True

        attr_name = EXCHANGES[name]
        try:
            exchange_class = getattr(ccxt, attr_name, None)
            if exchange_class is None:
                raise AttributeError(f"Kutubxonada '{attr_name}' topilmadi. 'pip install --upgrade ccxt' qilib ko'ring.")
            self.exchange = exchange_class(params)
            api_status = "Ha" if api_key else "Yo'q (faqat o'qish)"
            logger.info(f"Birja: {name} | Testnet: {cfg.get('testnet', False)} | API: {api_status}")
        except AttributeError as e:
            logger.error(f"❌ CCXT Versiya xatosi: {e}")
            logger.warning("Bot hozircha faqat tahlil (Yahoo Finance) rejimida ishlaydi.")
            self.exchange = None
            self.name = 'yahoo'

    # ------------------------------------------------------------------
    # ASOSIY METOD: OHLCV
    # ------------------------------------------------------------------

    def fetch_ohlcv(self, symbol: str, timeframe: str,
                    limit: int = 300) -> Optional[pd.DataFrame]:
        """OHLCV ma'lumotlarini olish (Smarter Fallback System)"""

        # Agar yahoo/tradingview yoki ccxt yo'q bo'lsa → Fallback tizimi
        if self.exchange is None:
            if self.name == 'tradingview' and TV_AVAILABLE:
                res = self.tv.fetch_ohlcv(symbol, timeframe, limit)
                if res is not None: return res
                return self._yf_fetch(symbol, timeframe, limit) # Yahoo Backup
            
            # Asosiy: Yahoo, Zaxira: TradingView (agar mavjud bo'lsa)
            res = self._yf_fetch(symbol, timeframe, limit)
            if res is not None: return res
            if TV_AVAILABLE:
                return self.tv.fetch_ohlcv(symbol, timeframe, limit)
            return None

        # ccxt birjadan olishga urinish
        try:
            raw = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            if raw:
                df = pd.DataFrame(
                    raw, columns=['timestamp','open','high','low','close','volume']
                )
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)
                df.set_index('timestamp', inplace=True)
                df = df.astype(float)
                if len(df) >= 10:
                    logger.debug(f"ccxt {symbol} {timeframe}: {len(df)} bar")
                    return df
        except Exception as e:
            logger.warning(f"ccxt xato ({symbol}): {e} → Yahoo Finance bilan urinmoqda")

        # ccxt ishlamasa → Yahoo Finance zaxira
        return self._yf_fetch(symbol, timeframe, limit)

    def _get_yf_ticker(self, yf_symbol: str):
        """Ticker obyektini keshdan olish yoki yaratish"""
        if yf_symbol not in self._ticker_cache:
            self._ticker_cache[yf_symbol] = yf.Ticker(yf_symbol)
        return self._ticker_cache[yf_symbol]

    def _yf_fetch(self, symbol: str, timeframe: str, limit: int = 300) -> Optional[pd.DataFrame]:
        """Yahoo Finance dan OHLCV"""
        if not YF_AVAILABLE:
            return None

        yf_sym = YF_SYMBOL_MAP.get(symbol.upper(), None)
        if not yf_sym:
            # Agar mapping yo'q bo'lsa → kripto sifatida qabul qil
            base = symbol.upper().replace('/USDT','').replace('/USD','')
            yf_sym = f"{base}-USD"

        yf_interval = YF_INTERVAL_MAP.get(timeframe, '5m')
        yf_period   = YF_PERIOD_MAP.get(yf_interval, '60d')

        try:
            ticker = self._get_yf_ticker(yf_sym)
            
            # 1m va 5m uchun faqat 7 kunlik ma'lumot olish (tezroq va barqaror)
            period = '7d' if yf_interval in ('1m','5m') else yf_period
            
            # Intermittent TypeError: 'NoneType' object is not subscriptable xatosi uchun
            df = None
            for attempt in range(2): # 2 marta urinib ko'risk
                try:
                    df = ticker.history(period=period, interval=yf_interval, auto_adjust=False)
                    if df is not None and not df.empty:
                        break
                except (TypeError, Exception) as e:
                    if attempt == 0:
                        time.sleep(2) # Kichik tanaffus
                        continue
                    else:
                        raise e
            
            if df is None or not hasattr(df, 'empty') or df.empty:
                logger.warning(f"YF {symbol} ({yf_sym}): bo'sh ma'lumot keldi")
                return None

            # MultiIndex va Column tozalash
            df = df.copy()
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(-1)
            
            df.columns = [str(c).lower().strip() for c in df.columns]
            
            final_df = pd.DataFrame(index=df.index)
            col_map = {
                'open': 'open', 'high': 'high', 'low': 'low', 
                'volume': 'volume', 'close': 'close', 
                'adj close': 'close', 'adjclose': 'close'
            }
            
            for src, dst in col_map.items():
                if src in df.columns:
                    val = df[src]
                    if isinstance(val, pd.DataFrame):
                        final_df[dst] = val.iloc[:, 0]
                    else:
                        final_df[dst] = val
            
            if 'close' not in final_df.columns or final_df.empty:
                logger.warning(f"YF {symbol}: 'close' ustuni topilmadi")
                return None

            df = final_df.copy()
            
            try:
                if df.index.tzinfo is None:
                    df.index = df.index.tz_localize('UTC')
                else:
                    df.index = df.index.tz_convert('UTC')
            except:
                pass
            
            if df is None or df.empty: return None
            
            df.columns = [c.lower() for c in df.columns]
            df.index.name = 'timestamp'
            df = df[['open','high','low','close','volume']]
            return df.astype(float)
        except Exception as e:
            logger.error(f"Yahoo Finance xato: {e}")
            return None

    # ------------------------------------------------------------------
    # IJRO ETISH METODLARI
    # ------------------------------------------------------------------

    def get_balance(self) -> Optional[dict]:
        """Birjadagi joriy balansni olish"""
        if self.exchange is None: return None
        try:
            return self.exchange.fetch_balance()
        except Exception as e:
            logger.error(f"Balans olishda xato: {e}")
            return None

    def create_order(self, symbol: str, side: str, amount: float,
                     price: float = None, sl: float = None, tp: float = None) -> Optional[dict]:
        """Order yaratish (Market yoki Limit)"""
        if self.exchange is None: 
            logger.error("API orqali savdo qilish uchun config'da 'exchange.name' ni belgilang (Binance/UzNEX)")
            return None
        
        try:
            params = {}
            if sl: params['stopLoss'] = sl
            if tp: params['takeProfit'] = tp
            
            if price:
                return self.exchange.create_limit_order(symbol, side, amount, price, params)
            else:
                return self.exchange.create_market_order(symbol, side, amount, params)
        except Exception as e:
            logger.error(f"Order yaratishda xato: {e}")
            return None
