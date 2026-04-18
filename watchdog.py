import os
import time
import subprocess
import sys
import logging
from datetime import datetime

# Logging setup for Watcher
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | WATCHDOG | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('Watchdog')

LOG_FILE = "logs/bot.log"
BOT_SCRIPT = "bot.py"
CHECK_INTERVAL = 60  # Har 1 daqiqada tekshirish
TIMEOUT = 600       # 10 daqiqa davomida log yangilanmasa = Restart

def get_last_log_time():
    if not os.path.exists(LOG_FILE):
        return time.time()
    return os.path.getmtime(LOG_FILE)

def start_bot():
    logger.info(f"Yangi bot jarayoni boshlanmoqda: {BOT_SCRIPT}")
    return subprocess.Popen([sys.executable, BOT_SCRIPT])

def main():
    logger.info("Gemini Watchdog Engine ishga tushdi.")
    
    bot_process = start_bot()
    
    while True:
        try:
            time.sleep(CHECK_INTERVAL)
            
            # 1. Jarayon o'lganini tekshirish
            if bot_process.poll() is not None:
                logger.warning("Bot jarayoni to'xtab qolgan! Qayta yuklanmoqda...")
                bot_process = start_bot()
                continue
            
            # 2. Log yangilanishini tekshirish (Hang detection)
            last_update = get_last_log_time()
            idle_time = time.time() - last_update
            
            if idle_time > TIMEOUT:
                logger.error(f"Bot 'muzlab' qolgan deb gumon qilinmoqda (Idle: {int(idle_time)}s). RESTART...")
                bot_process.terminate()
                time.sleep(5)
                if bot_process.poll() is None:
                    bot_process.kill()
                bot_process = start_bot()
            else:
                logger.info(f"Bot sog'lom. Idle: {int(idle_time)}s")
                
        except KeyboardInterrupt:
            logger.info("Watchdog to'xtatildi.")
            bot_process.terminate()
            break
        except Exception as e:
            logger.error(f"Watchdog xatosi: {e}")
            time.sleep(10)

if __name__ == "__main__":
    main()
