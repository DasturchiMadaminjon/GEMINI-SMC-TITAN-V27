import logging
from utils.position_sizer import format_position_line

class TradeManager:
    def __init__(self, config, db, notifier):
        self.cfg = config
        self.notifier = notifier
        self.loss_streak = 0

    def process_symbol_data(self, sym, df, state, lock, trend):
        from core.indicator import GeminiIndicator
        ind = GeminiIndicator(self.cfg)

        sig = ind.generate_signal(df, sym, "15m", self.loss_streak)

        if sig:
            balance  = state.get('terminal', {}).get('balance', 5000.0)
            risk_pct = float(self.cfg.get('trend', {}).get('risk_perc', 2.0))
            direction = "🟢 BUY (LONG)" if sig.direction == 'buy' else "🔴 SELL (SHORT)"

            pos_line = format_position_line(
                balance, risk_pct, sig.entry, sig.sl, sig.tp1, sig.tp2, sym
            )

            if self.cfg.get('trend', {}).get('fibo_split_enabled', True):
                e2 = sig.entry - (sig.entry - sig.sl) * 0.382

                msg  = f"🚀 <b>YANGI SIGNAL: {sym}</b>\n"
                msg += f"━━━━━━━━━━━━━━━━━━━━\n"
                msg += f"🔔 Signal: <b>{direction}</b>\n"
                msg += f"💎 Sifat: <code>{sig.quality:.1f}%</code>\n\n"
                msg += f"📥 1-Kirish: <code>{sig.entry:.5g}</code>\n"
                msg += f"📥 2-Kirish: <code>{e2:.5g}</code>\n"
                msg += f"🛡 Stop-Loss: <code>{sig.sl:.5g}</code>\n\n"
                msg += f"🎯 Maqsadlar:\n"
                msg += f"   1. TP1: <code>{sig.tp1:.5g}</code>\n"
                msg += f"   2. TP2: <code>{sig.tp2:.5g}</code>\n"
                msg += f"   3. TP3: <code>{sig.tp3:.5g}</code>\n\n"
                msg += f"🧠 <b>Asos:</b> {sig.reason}\n"
                msg += f"━━━━━━━━━━━━━━━━━━━━\n"
                msg += pos_line + "\n"
                msg += f"━━━━━━━━━━━━━━━━━━━━\n"
                msg += f"⚡ Titan V27.2 Master"
            else:
                msg = f"🚀 Signal: {sym} @ {sig.entry}\nSL: {sig.sl}\n{pos_line}"

            self.notifier.telegram.send(msg)

    def handle_loss(self):
        self.loss_streak += 1

    def handle_win(self):
        self.loss_streak = 0
