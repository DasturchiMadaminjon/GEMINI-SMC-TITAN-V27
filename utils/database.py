import sqlite3
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path="logs/bot_data.db"):
        self.db_path = db_path
        self._init_db()

    def _get_conn(self):
        """SQLite ulanishini olish (Timeout bilan locklarni kamaytirish)"""
        return sqlite3.connect(self.db_path, timeout=30)

    def _execute_query(self, query, params=(), is_fetch=False):
        """Universal va bardoshli query bajaruvchi"""
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            if is_fetch:
                return cursor.fetchall()
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Database Query Error: {e}")
            return None
        finally:
            conn.close()

    def _init_db(self):
        """Baza va jadvallarni yaratish"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            # Savdo tarixi jadvali
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    time TEXT,
                    symbol TEXT,
                    side TEXT,
                    entry REAL,
                    result TEXT,
                    r_gain REAL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            # Bot holati (optional) jadvali
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS stats (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            ''')
            # AI Chat tarixi jadvali (super_bot mantiqi)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS chat_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    role TEXT,
                    content TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            # Signallar logi (Tahlil uchun)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS signals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    time TEXT,
                    symbol TEXT,
                    direction TEXT,
                    entry REAL,
                    quality INTEGER,
                    reason TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
            logger.info("SQLite Baza ✅ Tayyor: " + self.db_path)
        except Exception as e:
            logger.error(f"Baza yaratishda xato: {e}")
        finally:
            conn.close()

    def add_history(self, time_str, symbol, is_buy, entry, result, r_gain):
        side = 'BUY' if is_buy else 'SELL'
        query = "INSERT INTO history (time, symbol, side, entry, result, r_gain) VALUES (?, ?, ?, ?, ?, ?)"
        self._execute_query(query, (time_str, symbol, side, entry, result, r_gain))

    def add_signal(self, time_str, symbol, direction, entry, quality, reason):
        """Signalni bazaga saqlash"""
        query = "INSERT INTO signals (time, symbol, direction, entry, quality, reason) VALUES (?, ?, ?, ?, ?, ?)"
        self._execute_query(query, (time_str, symbol, direction.upper(), entry, quality, reason))

    def get_history(self, limit=100):
        query = 'SELECT time, symbol, side, entry, result, r_gain FROM history ORDER BY id DESC LIMIT ?'
        rows = self._execute_query(query, (limit,), is_fetch=True)
        if not rows: return []
        
        history_list = []
        for r in rows:
            history_list.append({
                'time': r[0], 'symbol': r[1], 'buy': r[2] == 'BUY',
                'entry': r[3], 'result': r[4], 'r': r[5]
            })
        return history_list

    def add_chat_message(self, user_id, role, content, max_history=15):
        uid_str = str(user_id)
        # 1. Insert
        self._execute_query("INSERT INTO chat_history (user_id, role, content) VALUES (?, ?, ?)", (uid_str, role, content))
        # 2. Cleanup
        cleanup_query = '''
            DELETE FROM chat_history 
            WHERE id IN (
                SELECT id FROM chat_history 
                WHERE user_id = ? 
                ORDER BY id DESC LIMIT -1 OFFSET ?
            )
        '''
        self._execute_query(cleanup_query, (uid_str, max_history))

    def get_chat_history(self, user_id, limit=15):
        query = 'SELECT role, content FROM chat_history WHERE user_id = ? ORDER BY id ASC LIMIT ?'
        rows = self._execute_query(query, (str(user_id), limit), is_fetch=True)
        if not rows: return []
        return [{'role': r[0], 'content': r[1]} for r in rows]
