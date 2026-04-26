#!/bin/bash
BOT_DIR="$HOME/signal_v_27"
LOG_FILE="$BOT_DIR/logs/keeper.log"

# Xatosiz va aniq ishlashi uchun to'g'ridan-to'g'ri python3.13 ga bog'laymiz
VENV="python3.13"

mkdir -p "$BOT_DIR/logs"
echo "🚀 [$(date '+%Y-%m-%d %H:%M:%S')] Titan Bot Keeper ishga tushdi..." | tee -a "$LOG_FILE"
while true; do
    echo "⚡ [$(date '+%Y-%m-%d %H:%M:%S')] bot.py ishga tushirilmoqda..." | tee -a "$LOG_FILE"
    
    # Endi xatoliklar ham yashirinmaydi, ham faylga yoziladi, ham ekranga chiqadi
    cd "$BOT_DIR" && $VENV bot.py 2>&1 | tee -a "$LOG_FILE"
    
    EXIT_CODE=${PIPESTATUS[0]}
    if [ $EXIT_CODE -eq 0 ]; then
        echo "✅ [$(date '+%Y-%m-%d %H:%M:%S')] Bot to'xtadi." | tee -a "$LOG_FILE"
    else
        echo "⚠️ [$(date '+%Y-%m-%d %H:%M:%S')] Crash (exit $EXIT_CODE). 5s kutish..." | tee -a "$LOG_FILE"
    fi
    sleep 5
done
