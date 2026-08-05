from flask import Flask, request
import requests
import urllib.parse
import re
import os

app = Flask(__name__)

# तुमचे सिक्रेट्स आणि सेटिंग्ज
BOT_TOKEN = os.environ.get("BOT_TOKEN")

# --- अनेक ॲडमिन्ससाठी नवीन बदल ---
admin_env = os.environ.get("ADMIN_ID", "123456789")
ADMIN_IDS = [int(x.strip()) for x in admin_env.split(",") if x.strip()] 

TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# शॉर्टनरची सेटिंग आणि API (बॉट चालू असताना बदलण्यासाठी)
SETTINGS = {
    "SHORTENER_ON": True,
    "API_KEY": os.environ.get("NOWSHORT_API", "fb651ac52240c7865717bc46a105eb8a0d7246e1")
}
WAITING_FOR_API = {}

# एन्क्रिप्शन लॉजिक
CHAR_MAP = {'A':'Z', 'Z':'A', 'B':'Y', 'Y':'B', 'C':'X', 'X':'C', 'D':'W', 'W':'D', 'E':'V', 'V':'E', 'F':'U', 'U':'F', 'G':'T', 'T':'G', 'H':'S', 'S':'H', 'I':'R', 'R':'I', 'J':'Q', 'Q':'J', 'K':'P', 'P':'K', 'L':'O', 'O':'L', 'M':'N', 'N':'M', 'a':'z', 'z':'a', 'b':'y', 'y':'b', 'c':'x', 'x':'c', 'd':'w', 'w':'d', 'e':'v', 'v':'e', 'f':'u', 'u':'f', 'g':'t', 't':'g', 'h':'s', 's':'h', 'i':'r', 'r':'i', 'j':'q', 'q':'j', 'k':'p', 'p':'k', 'l':'o', 'o':'l', 'm':'n', 'n':'m', '0':'9', '9':'0', '1':'8', '8':'1', '2':'7', '7':'2', '3':'6', '6':'3', '4':'5', '5':'4'}

def encrypt_id(short_id):
    return "".join(CHAR_MAP.get(c, c) for c in short_id)

def format_sc(text):
    normal = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    small_caps = "ᴀʙᴄᴅᴇғɢʜɪᴊᴋʟᴍɴᴏᴘǫʀsᴛᴜᴠᴡxʏᴢᴀʙᴄᴅᴇғɢʜɪᴊᴋʟᴍɴᴏᴘǫʀsᴛᴜᴠᴡxʏᴢ"
    formatted = text.translate(str.maketrans(normal, small_caps))
    return f"<b>{formatted}</b>"

def send_message(chat_id, text, reply_to=None, reply_markup=None):
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True}
    if reply_to: payload["reply_to_message_id"] = reply_to
    if reply_markup: payload["reply_markup"] = reply_markup
    res = requests.post(f"{TELEGRAM_API_URL}/sendMessage", json=payload).json()
    return res.get("result", {}).get("message_id")

def edit_message(chat_id, message_id, text, reply_markup=None):
    payload = {"chat_id": chat_id, "message_id": message_id, "text": text, "parse_mode": "HTML"}
    if reply_markup: payload["reply_markup"] = reply_markup
    requests.post(f"{TELEGRAM_API_URL}/editMessageText", json=payload)

def delete_message(chat_id, message_id):
    requests.post(f"{TELEGRAM_API_URL}/deleteMessage", json={"chat_id": chat_id, "message_id": message_id})

def answer_callback(callback_query_id, text, show_alert=False):
    payload = {"callback_query_id": callback_query_id, "text": text, "show_alert": show_alert}
    requests.post(f"{TELEGRAM_API_URL}/answerCallbackQuery", json=payload)

def get_admin_keyboard():
    status = "🟢 ᴏɴ" if SETTINGS["SHORTENER_ON"] else "🔴 ᴏғғ"
    return {
        "inline_keyboard": [
            [{"text": f"⚙️ sʜᴏʀᴛᴇɴᴇʀ : {status}", "callback_data": "toggle_shortener"}],
            [{"text": "🔑 ᴄʜᴀɴɢᴇ ᴀᴘɪ ᴋᴇʏ", "callback_data": "change_api"}],
            [{"text": "❌ ᴄʟᴏsᴇ ᴘᴀɴᴇʟ", "callback_data": "close_panel"}]
        ]
    }

@app.route('/set_webhook', methods=['GET'])
def set_webhook():
    webhook_url = request.url_root.replace("http://", "https://")
    res = requests.get(f"{TELEGRAM_API_URL}/setWebhook?url={webhook_url}")
    return f"Webhook Setup Response: {res.text}"

@app.route('/', methods=['POST'])
def webhook():
    update = request.get_json()

    if "callback_query" in update:
        cb = update["callback_query"]
        chat_id = cb["message"]["chat"]["id"]
        user_id = cb["from"]["id"]
        msg_id = cb["message"]["message_id"]
        data = cb["data"]
        cb_id = cb["id"]

        if user_id not in ADMIN_IDS:
            answer_callback(cb_id, "You are not authorized!", True)
            return "OK", 200

        if data == "toggle_shortener":
            SETTINGS["SHORTENER_ON"] = not SETTINGS["SHORTENER_ON"]
            edit_message(chat_id, msg_id, format_sc("Admin Control Panel :"), get_admin_keyboard())
            answer_callback(cb_id, "Status Changed!")
        elif data == "change_api":
            WAITING_FOR_API[user_id] = True
            edit_message(chat_id, msg_id, format_sc("Please send the new API Key now..."))
            answer_callback(cb_id, "Waiting for API...")
        elif data == "close_panel":
            delete_message(chat_id, msg_id)
            answer_callback(cb_id, "Panel Closed")
        return "OK", 200

    if "message" in update:
        msg = update["message"]
        text = msg.get("caption") or msg.get("text")
        if not text: return "OK", 200

        chat_id = msg["chat"]["id"]
        msg_id = msg["message_id"]
        user_id = msg["from"]["id"]

        if WAITING_FOR_API.get(user_id) and user_id in ADMIN_IDS:
            SETTINGS["API_KEY"] = text.strip()
            WAITING_FOR_API[user_id] = False
            send_message(chat_id, f"✅ {format_sc('API Key Updated Successfully!')}")
            return "OK", 200

        if text == "/admin":
            if user_id in ADMIN_IDS:
                send_message(chat_id, format_sc("Admin Control Panel :"), reply_markup=get_admin_keyboard())
            else:
                send_message(chat_id, format_sc("You are not authorized!"))
            return "OK", 200

        if text == "/start":
            send_message(chat_id, format_sc("Welcome! Paste your movie links below."))
            return "OK", 200

        urls = re.findall(r'(https?://[^\s]+)', text)
        if urls:
            proc_msg_id = send_message(chat_id, f"⏳ {format_sc('Processing links...')}")
            new_text = text

            for url in urls[:5]:
                if "mtchannels.github.io" not in url and "t.me/LinkOpenNow" not in url:
                    try:
                        if SETTINGS["SHORTENER_ON"]:
                            api_url = f"https://nowshort.com/api?api={SETTINGS['API_KEY']}&url={urllib.parse.quote(url)}"
                            res = requests.get(api_url).json()
                            if "shortenedUrl" in res:
                                target_id = res["shortenedUrl"].split("nowshort.com/")[1]
                            else:
                                continue
                        else:
                            target_id = url
                            
                        enc_id = encrypt_id(target_id)
                        new_text = new_text.replace(url, f"https://mtc-go.vercel.app/s/{enc_id}")
                    except: continue

            if "photo" in msg:
                photo_id = msg["photo"][-1]["file_id"]
                payload = {"chat_id": chat_id, "photo": photo_id, "caption": new_text, "parse_mode": "HTML"}
                requests.post(f"{TELEGRAM_API_URL}/sendPhoto", json=payload)
            else:
                send_message(chat_id, new_text, reply_to=msg_id)

            send_message(chat_id, f"✅ {format_sc('Generated Successfully!')}")
            delete_message(chat_id, proc_msg_id)

    return "OK", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
