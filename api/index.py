from flask import Flask, request
import requests
import urllib.parse

app = Flask(__name__)

# तुमचे सिक्रेट्स 
BOT_TOKEN = "8781011517:AAHmZalssyKyEbbRogWVkqv4iiis1Rp_Fsk"
NOWSHORT_API = "fb651ac52240c7865717bc46a105eb8a0d7246e1"
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# तुमचे MTC चे एन्क्रिप्शन लॉजिक
CHAR_MAP = {'A':'Z', 'Z':'A', 'B':'Y', 'Y':'B', 'C':'X', 'X':'C', 'D':'W', 'W':'D', 'E':'V', 'V':'E', 'F':'U', 'U':'F', 'G':'T', 'T':'G', 'H':'S', 'S':'H', 'I':'R', 'R':'I', 'J':'Q', 'Q':'J', 'K':'P', 'P':'K', 'L':'O', 'O':'L', 'M':'N', 'N':'M', 'a':'z', 'z':'a', 'b':'y', 'y':'b', 'c':'x', 'x':'c', 'd':'w', 'w':'d', 'e':'v', 'v':'e', 'f':'u', 'u':'f', 'g':'t', 't':'g', 'h':'s', 's':'h', 'i':'r', 'r':'i', 'j':'q', 'q':'j', 'k':'p', 'p':'k', 'l':'o', 'o':'l', 'm':'n', 'n':'m', '0':'9', '9':'0', '1':'8', '8':'1', '2':'7', '7':'2', '3':'6', '6':'3', '4':'5', '5':'4'}

def encrypt_id(short_id):
    return "".join(CHAR_MAP.get(c, c) for c in short_id)

def send_message(chat_id, text):
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    requests.post(f"{TELEGRAM_API_URL}/sendMessage", json=payload)

@app.route('/', defaults={'path': ''}, methods=['POST', 'GET'])
@app.route('/<path:path>', methods=['POST', 'GET'])
def webhook(path):
    if request.method == 'GET':
        return "MTC Bot is running fast on Vercel! 🚀"
    
    try:
        update = request.get_json()
        if "message" in update and "text" in update["message"]:
            chat_id = update["message"]["chat"]["id"]
            text = update["message"]["text"].strip()
            
            if text == "/start":
                send_message(chat_id, "<b>Welcome to MTC Link Generator!</b> 🚀\n\nPaste your Telegram bot link or Terabox link below:")
                return "OK", 200

            target_url = ""
            
            if "start=" in text:
                code = text.split("start=")[1].split(" ")[0]
                target_url = "https://mtcprotect.blogspot.com/p/telegram-redirect.html?start=" + code
            elif text.startswith("http"):
                target_url = text
            
            if target_url:
                send_message(chat_id, "⏳ <i>Processing...</i>")
                try:
                    api_url = f"https://nowshort.com/api?api={NOWSHORT_API}&url={urllib.parse.quote(target_url)}"
                    res = requests.get(api_url)
                    data = res.json()
                    
                    if "shortenedUrl" in data:
                        short_id = data["shortenedUrl"].split("nowshort.com/")[1]
                        enc_id = encrypt_id(short_id)
                        final_link = f"https://mtc-go.vercel.app/s/{enc_id}"
                        
                        send_message(chat_id, f"✅ <b>Generated Successfully!</b>\n\n<code>{final_link}</code>\n\n(Tap the link to copy)")
                    else:
                        send_message(chat_id, "❌ Error: Could not generate link from NowShort.")
                except Exception as e:
                    send_message(chat_id, "❌ System Error during conversion.")
            else:
                send_message(chat_id, "⚠️ Please send a valid Telegram or Terabox link.")
    except Exception as e:
        pass
        
    return "OK", 200
