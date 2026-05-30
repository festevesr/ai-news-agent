# 🤖 Daily AI News Agent

A fully automated agent that fetches the latest AI news every morning, summarizes it using Google Gemini, and delivers a formatted HTML digest to your inbox — completely free.

---

## 📋 Overview

This project is a Python-based AI agent that runs automatically every day at 8:00 AM (Lima, Peru / UTC-5) using GitHub Actions. It requires no server, no paid subscriptions, and no computer to be left on.

### How it works

```
Google News RSS → Fetch full article text → Gemini 3.1 Flash Lite → HTML Email
```

1. **Fetches** the top 15 AI headlines from Google News RSS
2. **Scrapes** the full text of each article
3. **Sends** the content to Google Gemini for deep summarization
4. **Delivers** a styled HTML email with the top 5 stories of the day

---

## ✨ Features

- 📰 **Full article summarization** — Gemini reads the actual article, not just the headline
- 💡 **Why it matters** — explains the significance of each story
- 🔍 **Key detail** — surfaces one concrete fact most people would miss
- 🌐 **Big Picture** — a 2-sentence trend summary of the day's AI news
- 🔗 **Clickable links** — each story links directly to the original article
- 🎨 **HTML email** — clean, styled digest with no raw markdown symbols
- ☁️ **Fully cloud-based** — runs on GitHub Actions, no local machine needed
- 🔒 **Secure** — all credentials stored as GitHub Secrets, never hardcoded

---

## 🛠️ Tech Stack

| Component | Tool | Cost |
|---|---|---|
| News source | Google News RSS | Free |
| Article scraping | BeautifulSoup4 + lxml | Free |
| AI summarization | Google Gemini 3.1 Flash Lite API | Free |
| Scheduler | GitHub Actions | Free |
| Email delivery | Gmail SMTP | Free |
| **Total** | | **$0** |

---

## 🚀 Setup Guide

### Prerequisites
- A Google account (for Gemini API + Gmail)
- A GitHub account

### 1. Get a Gemini API Key
1. Go to [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)
2. Sign in with your Google account
3. Click **"Create API key"**
4. Copy the key (starts with `AIza`)

### 2. Get a Gmail App Password
1. Go to your Google Account → **Security** → **2-Step Verification** (enable it)
2. Go to **Security** → **App Passwords**
3. Select "Mail" and generate a 16-character password
4. Save it — you'll only see it once

### 3. Configure GitHub Secrets
In your repository go to **Settings → Secrets and variables → Actions** and add:

| Secret Name | Description |
|---|---|
| `GEMINI_API_KEY` | Your Gemini API key |
| `GMAIL_USER` | Your Gmail address |
| `GMAIL_PASSWORD` | Your 16-char Gmail App Password |
| `TO_EMAIL` | Email address to receive the digest |
| `NEWS_RSS_URL` | Google News RSS URL (see below) |

**Recommended RSS URL:**
```
https://news.google.com/rss/search?q=artificial+intelligence+OR+LLM+OR+generative+AI&hl=en-US&gl=US&ceid=US:en
```

### 4. Done!
The agent will run automatically every day at 8:00 AM Lima time. To test it manually:

**Actions → Daily AI News Digest → Run workflow**

---

## 🗂️ Project Structure

```
ai-news-agent/
├── agent.py                        # Main script
├── requirements.txt                # Python dependencies
├── README.md                       # This file
└── .github/
    └── workflows/
        └── daily_news.yml          # GitHub Actions scheduler
```

---

## 💻 Running Locally

### 1. Clone the repository
```bash
git clone https://github.com/your-username/ai-news-agent.git
cd ai-news-agent
```

### 2. Create and activate a virtual environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Create a `.env` file
```
GEMINI_API_KEY=your-gemini-api-key
GMAIL_USER=your_email@gmail.com
GMAIL_PASSWORD=xxxx xxxx xxxx xxxx
TO_EMAIL=destination@gmail.com
NEWS_RSS_URL=https://news.google.com/rss/search?q=artificial+intelligence+OR+LLM+OR+generative+AI&hl=en-US&gl=US&ceid=US:en
```

> ⚠️ The `.env` file is listed in `.gitignore` and will never be pushed to GitHub.

### 5. Run the agent
```bash
python agent.py
```

---

## ⚙️ Customization

### Change the delivery time
Edit the cron expression in `.github/workflows/daily_news.yml`:
```yaml
- cron: '0 13 * * *'   # 13:00 UTC = 8:00 AM Lima (UTC-5)
```
Use [crontab.guru](https://crontab.guru) to calculate the UTC time for your timezone.

### Change the news topic
Replace the `NEWS_RSS_URL` secret with any Google News RSS feed. For example:
- **AI + Robotics:** `q=artificial+intelligence+OR+robotics`
- **AI + Business:** `q=artificial+intelligence+OR+AI+startup+OR+venture+capital`
- **General Tech:** `q=technology+OR+silicon+valley+OR+big+tech`

### Change the number of articles fetched
In `agent.py`, find this line and adjust the number:
```python
items = root.findall(".//item")[:15]   # change 15 to any number
```

---

## ⚠️ Important Notes

- **GitHub disables scheduled workflows after 60 days of repo inactivity.** To prevent this, trigger a manual run once a month from the Actions tab.
- Some news websites block scrapers. If an article can't be fetched, the agent falls back to summarizing the headline only — the email will still send.
- The Gemini free tier allows up to 15 requests per minute — well above what this agent needs (1 request per day).

---

## 🗺️ Roadmap

- [x] Basic headline fetching and summarization
- [x] Full article text scraping
- [x] HTML email formatting
- [ ] Multiple news sources (MIT Tech Review, ArXiv, The Batch)
- [ ] Memory — avoid repeating stories across days
- [ ] Weekly summary digest
- [ ] Telegram / Slack delivery
- [ ] RAG — ask questions about your news archive

---

## 📄 License

MIT License — free to use, modify, and distribute.
