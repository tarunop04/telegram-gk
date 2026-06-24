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

### Step 4 — Claude API key lo
- [platform.claude.com](https://platform.claude.com) → API key banao (`sk-ant-...`).

---

## 🚀 GitHub par deploy (recommended — 24/7 free)

1. Ek **naya GitHub repo** banao aur ye saari files usme daal do (push karo).
2. Repo me jao → **Settings → Secrets and variables → Actions → New repository secret**.
   Ye 4 secrets add karo:

   | Secret name | Value |
   |---|---|
   | `ANTHROPIC_API_KEY` | tumhari Claude key |
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

## 💰 Cost kam karna ho to
Default model `claude-opus-4-8` hai (best quality). Sasta chahiye to
`MODEL=claude-haiku-4-5` set kar do — workflow file me commented line uncomment
karo, ya secret/env me `MODEL` daal do.

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
