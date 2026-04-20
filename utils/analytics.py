import json

def generate_trade_report(bot_state):
    """
    Tarixiy signallarni o'qib, AI tahlili uchun matnli hisobot yaratadi.
    Faqat eng so'nggi 50 ta bitim hisoboti saqlanadi (xotirani tejash uchun).
    """
    signals = bot_state.get('signals_log', [])
    if not signals:
        return "Bot hozircha hech qanday signal ishlamagan. Barcha ma'lumotlar nolda turibdi."

    # FAKAT eng oxirgi 50 ta signalni o'qib xulosa yozamiz
    recent_signals = signals[-50:]
    
    total = len(recent_signals)
    success = sum(1 for s in recent_signals if s.get('outcome') == 'win')
    loss = sum(1 for s in recent_signals if s.get('outcome') == 'loss')
    pending = total - success - loss
    
    report_text = f"XISOBOOT TAQDIM ETILDI:\n- Jami Signallar (So'nggi o'qilganlar): {total}\n"
    report_text += f"- Foydali (Win): {success}\n- Zararli (Loss): {loss}\n- Kutilayotgan (Pending): {pending}\n\n"
    report_text += "SO'NGGI 10 BITIM TAPHSILOTI:\n"

    for i, s in enumerate(recent_signals[-10:]):
        report_text += f"{i+1}. {s.get('symbol')} | {s.get('direction', 'BUY')} @ {s.get('entry')} | {s.get('outcome', 'kutilmoqda')}\n"

    report_text += "\nUShbu statistikani o'qib fond menejeri sifatida qisqa xulosa bering va kelasi xaftaga strategik tavsiya tugiting."
    return report_text
