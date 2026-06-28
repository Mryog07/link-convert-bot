from flask import Flask, request
import requests
import urllib.parse
import re

app = Flask(__name__)

BOT_TOKEN = "8781011517:AAHmZalssyKyEbbRogWVkqv4iiis1Rp_Fsk"
NOWSHORT_API = "fb651ac52240c7865717bc46a105eb8a0d7246e1"
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

CHAR_MAP = {'A':'Z', 'Z':'A', 'B':'Y', 'Y':'B', 'C':'X', 'X':'C', 'D':'W', 'W':'D', 'E':'V', 'V':'E', 'F':'U', 'U':'F', 'G':'T', 'T':'G', 'H':'S', 'S':'H', 'I':'R', 'R':'I', 'J':'Q', 'Q':'J', 'K':'P', 'P':'K', 'L':'O', 'O':'L', 'M':'N', 'N':'M', 'a':'z', 'z':'a', 'b':'y', 'y':'b', 'c':'x', 'x':'c', 'd':'w', 'w':'d', 'e':'v', 'v':'e', 'f':'u', 'u':'f', 'g':'t', 't':'g', 'h':'s', 's':'h', 'i':'r', 'r':'i', 'j':'q', 'q':'j', 'k':'p', 'p':'k', 'l':'o', 'o':'l', 'm':'n', 'n':'m', '0':'9', '9':'0', '1':'8', '8':'1', '2':'7', '7':'2', '3':'6', '6':'3', '4':'5', '5':'4'}

def encrypt_id(short_id):
    return "".join(CHAR_MAP.get(c, c) for c in short_id)

def send_message(chat_id, text, reply_to=None):
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True}
    if reply_to: payload["reply_to_message_id"] = reply_to
    res = requests.post(f"{TELEGRAM_API_URL}/sendMessage", json=payload).json()
    return res.get("result", {}).get("message_id")

def delete_message(chat_id, message_id):
    requests.post(f"{TELEGRAM_API_URL}/deleteMessage", json={"chat_id": chat_id, "message_id": message_id})

@app.route('/', methods=['POST'])
def webhook():
    update = request.get_json()
    if "message" in update and "text" in update["message"]:
        chat_id = update["message"]["chat"]["id"]
        msg_id = update["message"]["message_id"]
        text = update["message"]["text"]
        
        if text == "/start":
            send_message(chat_id, "<b>Welcome!</b> Paste your movie links below.")
            return "OK", 200

        urls = re.findall(r'(https?://[^\s]+)', text)
        if urls:
            proc_msg_id = send_message(chat_id, "⏳ <i>Processing...</i>")
            new_text = text
            for url in urls[:5]:
                if "mtchannels.github.io" not in url and "t.me/LinkOpenNow" not in url:
                    try:
                        api_url = f"https://nowshort.com/api?api={NOWSHORT_API}&url={urllib.parse.quote(url)}"
                        res = requests.get(api_url).json()
                        if "shortenedUrl" in res:
                            enc_id = encrypt_id(res["shortenedUrl"].split("nowshort.com/")[1])
                            new_text = new_text.replace(url, f"https://mtc-go.vercel.app/s/{enc_id}")
                    except: continue
            
            # मूळ पोस्ट जशीच्या तशी पाठवणे
            send_message(chat_id, new_text, reply_to=msg_id)
            # Generated चा मेसेज वेगळा पाठवणे
            send_message(chat_id, "✅ <b>Generated Successfully!</b>")
            delete_message(chat_id, proc_msg_id)
            
    return "OK", 200
