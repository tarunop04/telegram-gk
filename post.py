"""
Telegram GK/Current Affairs auto-poster.

Flow:
  1. Claude (claude-opus-4-8) se ek "Daily GK" post + ek quiz question generate karte hain.
  2. Post ko Telegram channel aur group dono me bhejte hain.
  3. Quiz ko Telegram ke native poll (quiz mode) ke roop me bhejte hain.
  4. Recent quiz questions history.json me save karte hain taaki repeat na ho.

Environment variables (GitHub Actions secrets ya local .env):
  ANTHROPIC_API_KEY   - Claude API key
  TELEGRAM_BOT_TOKEN  - BotFather se mila bot token
  CHANNEL_ID          - channel ka @username ya -100... numeric id
  GROUP_ID            - group ka -100... numeric id (optional)
  MODEL               - (optional) default: claude-opus-4-8
                        Sasta chahiye to: claude-haiku-4-5
  TOPIC               - (optional) content ka focus, default neeche SUBJECT me
"""

import json
import os
import sys
from pathlib import Path

import anthropic
import requests


def _load_dotenv():
    """Local testing ke liye .env padh leta hai (GitHub par secrets aate hain)."""
    env_path = Path(__file__).parent / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


_load_dotenv()

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

MODEL = os.environ.get("MODEL", "claude-opus-4-8")
SUBJECT = os.environ.get("TOPIC", "Indian GK aur Current Affairs (competitive exams: SSC, UPSC, Banking, Railway)")

HISTORY_FILE = Path(__file__).parent / "history.json"
MAX_HISTORY = 60  # itne purane sawaal yaad rakhte hain repeat rokne ke liye

TELEGRAM_API = "https://api.telegram.org/bot{token}/{method}"

# Claude se structured JSON manga rahe hain — parsing ki tension nahi.
OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "facts": {"type": "array", "items": {"type": "string"}},
        "quiz": {
            "type": "object",
            "properties": {
                "question": {"type": "string"},
                "options": {"type": "array", "items": {"type": "string"}},
                "correct_index": {"type": "integer"},
                "explanation": {"type": "string"},
            },
            "required": ["question", "options", "correct_index", "explanation"],
            "additionalProperties": False,
        },
    },
    "required": ["title", "facts", "quiz"],
    "additionalProperties": False,
}


# ---------------------------------------------------------------------------
# History (repeat rokne ke liye)
# ---------------------------------------------------------------------------

def load_history():
    if HISTORY_FILE.exists():
        try:
            return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []
    return []


def save_history(history):
    HISTORY_FILE.write_text(
        json.dumps(history[-MAX_HISTORY:], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# Claude se content generate karna
# ---------------------------------------------------------------------------

def generate_content(recent_questions):
    client = anthropic.Anthropic()  # ANTHROPIC_API_KEY env se uthata hai

    avoid = "\n".join(f"- {q}" for q in recent_questions[-40:]) or "(abhi tak koi nahi)"

    prompt = f"""Tum ek educational Telegram channel ke liye content bana rahe ho.
Topic: {SUBJECT}

Ek "Daily GK" post banao jisme:
- title: ek chhota aakarshak title (emoji ke saath)
- facts: 5 se 6 useful GK points. Har point Hindi me, par important keyword/naam English me bhi. Crisp rakho.
- quiz: ek multiple-choice question
    - question: 300 character se kam
    - options: bilkul 4 options, har ek 100 character se kam
    - correct_index: sahi option ka index (0-3)
    - explanation: 1-2 line me sahi jawab kyun (Hindi)

Content factually accurate hona chahiye. Jaane-maane, verifiable facts hi do —
koi anuman ya galat tareekh/naam mat do.

Ye sawaal pehle aa chuke hain, inhe dobara mat poochho (alag topic/sawaal banao):
{avoid}
"""

    resp = client.messages.create(
        model=MODEL,
        max_tokens=2000,
        thinking={"type": "adaptive"},
        output_config={"format": {"type": "json_schema", "schema": OUTPUT_SCHEMA}},
        messages=[{"role": "user", "content": prompt}],
    )

    text = next(b.text for b in resp.content if b.type == "text")
    return json.loads(text)


# ---------------------------------------------------------------------------
# Telegram helpers
# ---------------------------------------------------------------------------

def tg_call(method, payload):
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    url = TELEGRAM_API.format(token=token, method=method)
    r = requests.post(url, json=payload, timeout=30)
    data = r.json()
    if not data.get("ok"):
        raise RuntimeError(f"Telegram {method} fail: {data}")
    return data["result"]


def format_post(content):
    lines = [f"<b>{content['title']}</b>", ""]
    for fact in content["facts"]:
        lines.append(f"• {fact}")
    lines.append("")
    lines.append("📚 Aur sawaalon ke liye humse jude rahiye!")
    return "\n".join(lines)


def send_text(chat_id, text):
    tg_call("sendMessage", {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    })


def send_quiz(chat_id, quiz):
    # Telegram limits: question <=300, har option <=100, 2-10 options.
    options = [opt[:100] for opt in quiz["options"]]
    correct = quiz["correct_index"]
    if not (0 <= correct < len(options)):
        correct = 0
    tg_call("sendPoll", {
        "chat_id": chat_id,
        "question": quiz["question"][:300],
        "options": options,
        "type": "quiz",
        "correct_option_id": correct,
        "explanation": quiz["explanation"][:200],
        "is_anonymous": True,
    })


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    history = load_history()
    print("Claude se content generate kar rahe hain...")
    content = generate_content(history)

    post_text = format_post(content)
    quiz = content["quiz"]

    targets = []
    if os.environ.get("CHANNEL_ID"):
        targets.append(os.environ["CHANNEL_ID"])
    if os.environ.get("GROUP_ID"):
        targets.append(os.environ["GROUP_ID"])

    if not targets:
        print("ERROR: CHANNEL_ID ya GROUP_ID set nahi hai.", file=sys.stderr)
        sys.exit(1)

    for chat_id in targets:
        print(f"Post bhej rahe hain -> {chat_id}")
        send_text(chat_id, post_text)
        send_quiz(chat_id, quiz)

    history.append(quiz["question"])
    save_history(history)
    print("Done ✅")


if __name__ == "__main__":
    main()
