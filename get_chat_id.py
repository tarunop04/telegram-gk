"""
Helper: channel/group ki chat ID nikalne ke liye.

Kaise use karein:
  1. Apne bot ko channel aur group dono me ADMIN bana do.
  2. Group me koi bhi message bhejo, aur channel me ek post daalo.
  3. TELEGRAM_BOT_TOKEN set karke ye script chalao:
        python get_chat_id.py
  4. Output me jo "id" dikhe (channel/group ke liye -100... se shuru),
     usse CHANNEL_ID / GROUP_ID me daal do.

Note: Channel ki id getUpdates me tabhi aati hai jab bot ne hal hi me
us channel ki koi update dekhi ho. Agar channel id na dikhe to channel ka
@username (jaise @mychannel) bhi CHANNEL_ID ke roop me chal jaata hai.
"""

import os
import requests

token = os.environ["TELEGRAM_BOT_TOKEN"]
r = requests.get(f"https://api.telegram.org/bot{token}/getUpdates", timeout=30)
data = r.json()

if not data.get("ok"):
    print("Error:", data)
    raise SystemExit(1)

seen = {}
for update in data["result"]:
    chat = (
        update.get("message", {}).get("chat")
        or update.get("channel_post", {}).get("chat")
        or update.get("my_chat_member", {}).get("chat")
    )
    if chat:
        seen[chat["id"]] = chat.get("title") or chat.get("username") or chat.get("type")

if not seen:
    print("Koi chat nahi mili. Pehle group me message bhejo / channel me post daalo,")
    print("phir dobara chalao. (Bot admin hona chahiye.)")
else:
    print("Mili hui chats:")
    for cid, name in seen.items():
        print(f"  {cid}  ->  {name}")
