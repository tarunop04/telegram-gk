"""
Telegram GK/Current Affairs auto-poster (OpenAI-compatible).

Flow:
  1. AI (OpenAI ya koi bhi OpenAI-compatible API jaise Groq) se ek "Daily GK"
     post + ek quiz question generate karte hain.
  2. Post ko Telegram channel aur group dono me bhejte hain.
  3. Quiz ko Telegram ke native poll (quiz mode) ke roop me bhejte hain.
  4. Recent quiz questions history.json me save karte hain taaki repeat na ho.

Environment variables (GitHub Actions secrets ya local .env):
  OPENAI_API_KEY      - OpenAI ya Groq ki API key
  OPENAI_BASE_URL     - (optional) Groq ke liye: https://api.groq.com/openai/v1
  OPENAI_MODEL        - (optional) default: gpt-4o-mini
                        Groq free model: llama-3.3-70b-versatile
  TELEGRAM_BOT_TOKEN  - BotFather se mila bot token
  CHANNEL_ID          - channel ka @username ya -100... numeric id
  GROUP_ID            - group ka -100... numeric id (optional)
  TOPIC               - (optional) content ka focus
"""

import json
import os
import sys
from pathlib import Path

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

MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
SUBJECT = os.environ.get(
    "TOPIC",
    "Indian GK aur Current Affairs (competitive exams: SSC, UPSC, Banking, Railway)",
)

HISTORY_FILE = Path(__file__).parent / "history.json"
BANK_FILE = Path(__file__).parent / "content_bank.json"
STATE_FILE = Path(__file__).parent / "state.json"
MAX_HISTORY = 60  # itne purane sawaal yaad rakhte hain repeat rokne ke liye

TELEGRAM_API = "https://api.telegram.org/bot{token}/{method}"


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
# Content source: bina key ke FREE content bank, ya AI (OpenAI/Groq)
# ---------------------------------------------------------------------------

def generate_content(recent_questions):
    """OPENAI_API_KEY ho to AI se, warna FREE built-in content bank se."""
    if os.environ.get("OPENAI_API_KEY"):
        return generate_with_ai(recent_questions)
    return pick_from_bank()


def pick_from_bank():
    bank = json.loads(BANK_FILE.read_text(encoding="utf-8"))
    if not bank:
        raise RuntimeError("content_bank.json khaali hai")
    idx = 0
    if STATE_FILE.exists():
        try:
            idx = json.loads(STATE_FILE.read_text(encoding="utf-8")).get("next_index", 0)
        except json.JSONDecodeError:
            idx = 0
    item = bank[idx % len(bank)]
    STATE_FILE.write_text(
        json.dumps({"next_index": (idx + 1) % len(bank)}, indent=2),
        encoding="utf-8",
    )
    return item


def generate_with_ai(recent_questions):
    from openai import OpenAI  # sirf AI-mode me zaroorat

    # base_url set ho to Groq/OpenRouter wagairah; warna OpenAI default.
    client = OpenAI(
        api_key=os.environ["OPENAI_API_KEY"],
        base_url=os.environ.get("OPENAI_BASE_URL") or None,
    )

    avoid = "\n".join(f"- {q}" for q in recent_questions[-40:]) or "(abhi tak koi nahi)"

    system_msg = (
        "Tum ek educational Telegram channel ke liye GK content likhne wale expert ho. "
        "Hamesha valid JSON me jawab dena."
    )

    user_msg = f"""Topic: {SUBJECT}

Ek "Daily GK" post banao aur SIRF is JSON format me do (aur kuch nahi):
{{
  "title": "ek chhota aakarshak title (emoji ke saath)",
  "facts": ["5 se 6 useful GK points, Hindi me, important keyword/naam English me bhi, crisp"],
  "quiz": {{
    "question": "ek MCQ sawaal (300 char se kam)",
    "options": ["bilkul 4 options, har ek 100 char se kam"],
    "correct_index": 0,
    "explanation": "sahi jawab kyun (1-2 line Hindi)"
  }}
}}

Niyam:
- Content factually accurate ho. Sirf jaane-maane, verifiable facts. Koi galat tareekh/naam mat do.
- quiz.options me bilkul 4 options ho.
- quiz.correct_index 0 se 3 ke beech ho.

Ye sawaal pehle aa chuke hain, inhe dobara mat poochho (alag sawaal banao):
{avoid}
"""

    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
        ],
        response_format={"type": "json_object"},
        temperature=0.9,
    )
    return json.loads(resp.choices[0].message.content)


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
    options = [str(opt)[:100] for opt in quiz["options"]][:10]
    correct = quiz.get("correct_index", 0)
    if not (0 <= correct < len(options)):
        correct = 0
    tg_call("sendPoll", {
        "chat_id": chat_id,
        "question": quiz["question"][:300],
        "options": options,
        "type": "quiz",
        "correct_option_id": correct,
        "explanation": quiz.get("explanation", "")[:200],
        "is_anonymous": True,
    })


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    history = load_history()
    mode = f"AI ({MODEL})" if os.environ.get("OPENAI_API_KEY") else "FREE content bank"
    print(f"Content source: {mode}")
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

    # Default: sirf quiz post hota hai. Facts wala post bhi chahiye to
    # POST_FACTS=1 set kar do.
    post_facts = os.environ.get("POST_FACTS", "0").lower() in ("1", "true", "yes", "on")
    for chat_id in targets:
        print(f"Quiz bhej rahe hain -> {chat_id}")
        if post_facts:
            send_text(chat_id, post_text)
        send_quiz(chat_id, quiz)

    history.append(quiz["question"])
    save_history(history)
    print("Done!")


if __name__ == "__main__":
    main()
