import json, os

STATE_FILE = "data/bot_state.json"

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"DEBUG: Xotirani o'qishda xatolik: {e}")
    return None

def save_state(state):
    # 'data' papkasi mavjud bo'lmasa, uni yaratish
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, 'w') as f:
        # Faylni inson o'qishi oson bo'lgan JSON formatida saqlaymiz
        json.dump(state, f, indent=4)
