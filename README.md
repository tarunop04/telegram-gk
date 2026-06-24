# 📚 Telegram GK Auto-Poster

Ek automation jo **Claude AI** se roz GK / Current Affairs content + quiz banata hai
aur tumhare **Telegram channel + group** me apne aap post kar deta hai —
**GitHub Actions** par 24/7 free chalta hai (PC band ho tab bhi).

Har run me jata hai:
- Ek "Daily GK" post (5-6 facts, Hindi me)
- Ek **native quiz poll** (sahi jawab + explanation ke saath)

---

## 🛠️ Setup (ek baar karna hai)

### Step 1 — Telegram Bot banao
1. Telegram me **@BotFather** kholo → `/newbot` bhejo.
2. Bot ka naam aur username do.
3. Jo **token** milega (jaise `123456:AAxx...`) usse safe rakho.

### Step 2 — Channel aur Group banao
1. Ek **channel** banao (jaha content post hoga).
2. Ek **group** banao (jaha log discuss karein) — optional.
3. **Apne bot ko dono me ADMIN** bana do (post karne ki permission ke saath).

### Step 3 — Chat ID nikalo
- **Channel** ke liye: agar channel public hai to uska `@username` hi kaafi hai.
- **Group** / private channel ke liye numeric id chahiye:
  1. Group me koi message bhejo / channel me ek post daalo.
  2. Token set karke ye chalao:
     ```bash
     python get_chat_id.py
     ```
  3. Output me jo `-100...` wali id dikhe, usse note kar lo.

### Step 4 — AI API key lo
Do option:
- **OpenAI (paid):** [platform.openai.com](https://platform.openai.com) → API key (`sk-...`). Account me thode credits daalne padte hain.
- **Groq (FREE):** [console.groq.com](https://console.groq.com) → free API key (`gsk_...`). Iske saath `OPENAI_BASE_URL=https://api.groq.com/openai/v1` aur `OPENAI_MODEL=llama-3.3-70b-versatile` bhi set karo.

---

## 🚀 GitHub par deploy (recommended — 24/7 free)

1. Ek **naya GitHub repo** banao aur ye saari files usme daal do (push karo).
2. Repo me jao → **Settings → Secrets and variables → Actions → New repository secret**.
   Ye 4 secrets add karo:

   | Secret name | Value |
   |---|---|
   | `OPENAI_API_KEY` | OpenAI ya Groq ki key |
   | `OPENAI_BASE_URL` | Groq use kar rahe ho to `https://api.groq.com/openai/v1` (OpenAI ke liye skip) |
   | `OPENAI_MODEL` | Groq: `llama-3.3-70b-versatile` (OpenAI ke liye skip) |
   | `TELEGRAM_BOT_TOKEN` | BotFather wala token |
   | `CHANNEL_ID` | `@yourchannel` ya `-100...` |
   | `GROUP_ID` | group ki `-100...` id (na ho to skip) |

3. **Actions** tab me jao → workflow enable karo.
4. Test ke liye: **Actions → "Telegram GK Auto Post" → Run workflow** dabao.
   Channel me post aa jaye to setup sahi hai ✅

Iske baad ye **roz subah 9 baje aur shaam 6 baje (IST)** apne aap post karega.
Time badalna ho to [`.github/workflows/post.yml`](.github/workflows/post.yml) me `cron`
edit kar do (yaad rahe time **UTC** me likhna hai, IST = UTC + 5:30).

---

## 💻 Local par test karna (optional)

```bash
pip install -r requirements.txt
cp .env.example .env      # phir .env me apni values bhar do
python post.py
```

---

## 💰 Free vs Paid
- **FREE:** Groq use karo (`OPENAI_BASE_URL` + `OPENAI_MODEL` set karke). Bilkul free.
- **Paid:** OpenAI key (best quality), default model `gpt-4o-mini` (bahut sasta). Badalna ho to `OPENAI_MODEL` set karo.

## ⚙️ Customize
- **Topic badalna:** `TOPIC` env var set karo (jaise `English Vocabulary` ya `Coding Tips`).
- **Frequency:** `post.yml` me `cron` lines add/remove karo.
- **Format:** `post.py` ke `format_post()` aur prompt me badlav karo.

---

## 📁 Files
| File | Kaam |
|---|---|
| `post.py` | content generate + Telegram par post |
| `get_chat_id.py` | channel/group ki id nikalna |
| `.github/workflows/post.yml` | GitHub Actions schedule |
| `history.json` | purane sawaal (repeat rokne ke liye) |
| `.env.example` | local config ka template |
