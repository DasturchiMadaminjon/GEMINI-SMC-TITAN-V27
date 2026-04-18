import os
from utils.persistence import load_state, save_state

def run_test():
    print("🔄 Persistence test boshlandi...")

    # 1. Soxta (test) holatini yaratamiz
    test_state = {
        'symbols': {'XAU/USD': {'price': 2500.5}},
        'terminal': {'balance': 5200.0},
        'ai_requests': [{'type': 'scalping', 'symbol': 'BTC/USDT'}],
        'loss_streak': 0
    }

    # 2. Xotiraga saqlaymiz
    save_state(test_state)
    print("✅ Xotira (bot_state.json) faylga muvaffaqiyatli saqlandi.")

    # 3. Fayldagi ma'lumotlarni qayta o'qiymiz
    loaded_state = load_state()
    print(f"📥 O'qilgan xotira: {loaded_state}")

    # 4. Solishtiramiz
    if loaded_state == test_state:
        print("\n🎉 SUPER NATIJA: Xotira saqlash va o'qish jarayoni 100% to'g'ri ishladi! Hech narsa yo'qolmadi.")
    else:
        print("\n❌ XATOLIK: O'qilgan ma'lumot saqlanganiga mos kelmadi.")

if __name__ == "__main__":
    run_test()
