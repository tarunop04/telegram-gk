"""
Telegram Jokes auto-poster — har ghante ek funny desi joke (Groq AI se, free).

Environment variables:
  OPENAI_API_KEY      - Groq (ya OpenAI) ki API key
  OPENAI_BASE_URL     - Groq: https://api.groq.com/openai/v1
  OPENAI_MODEL        - Groq: llama-3.3-70b-versatile
  TELEGRAM_BOT_TOKEN  - bot token
  JOKES_CHANNEL_ID    - jokes channel ka -100... id
"""

import json
import os
import sys
from pathlib import Path

import requests


def _load_dotenv():
    env_path = Path(__file__).parent / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        os.environ.setdefault(k.strip(), v.strip())


_load_dotenv()

MODEL = os.environ.get("OPENAI_MODEL", "llama-3.3-70b-versatile")
HISTORY_FILE = Path(__file__).parent / "jokes_history.json"
MAX_HISTORY = 80
TELEGRAM_API = "https://api.telegram.org/bot{token}/{method}"


def load_history():
    if HISTORY_FILE.exists():
        try:
            return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []
    return []


def save_history(h):
    HISTORY_FILE.write_text(
        json.dumps(h[-MAX_HISTORY:], ensure_ascii=False, indent=2), encoding="utf-8"
    )


def generate_joke(recent):
    from openai import OpenAI

    client = OpenAI(
        api_key=os.environ["OPENAI_API_KEY"],
        base_url=os.environ.get("OPENAI_BASE_URL") or None,
    )
    avoid = "\n".join(f"- {j[:60]}" for j in recent[-30:]) or "(koi nahi)"
    user_msg = f"""Ek chhota, original aur funny desi joke (chutkula) Hindi me likho.

Niyam:
- Sirf joke do, koi intro/explanation nahi.
- Thoda bold ya double-meaning chalega, par bhadda/explicit/gaali wala NAHI.
- 1-3 line ka rakho, punch achhi ho.
- Format: setup phir punchline.

Ye jokes pehle aa chuke, inse alag banao:
{avoid}
"""
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "Tum ek mazedaar desi comedian ho jo chutkule likhta hai."},
            {"role": "user", "content": user_msg},
        ],
        temperature=1.0,
        max_tokens=300,
    )
    return resp.choices[0].message.content.strip()


def send_text(chat_id, text):
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    url = TELEGRAM_API.format(token=token, method="sendMessage")
    r = requests.post(url, json={"chat_id": chat_id, "text": text}, timeout=30)
    data = r.json()
    if not data.get("ok"):
        raise RuntimeError(f"Telegram fail: {data}")


def main():
    chat_id = os.environ.get("JOKES_CHANNEL_ID")
    if not chat_id:
        print("ERROR: JOKES_CHANNEL_ID set nahi hai.", file=sys.stderr)
        sys.exit(1)

    history = load_history()
    print(f"Joke generate ({MODEL})...")
    joke = generate_joke(history)

    text = f"😂 {joke}\n\n— Daily Desi Jokes"
    send_text(chat_id, text)

    history.append(joke)
    save_history(history)
    print("Done!")


if __name__ == "__main__":
    main()
