# ============================================================
#  IMPORT LIBRARIES
# ============================================================

from dotenv import load_dotenv
load_dotenv()

import os
import requests
import smtplib
import xml.etree.ElementTree as ET
import json
import re
from google import genai
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from bs4 import BeautifulSoup
from datetime import date

# ============================================================
#  ENVIRONMENT CREDENTIALS
# ============================================================

GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
GMAIL_USER     = os.environ["GMAIL_USER"]
GMAIL_PASSWORD = os.environ["GMAIL_PASSWORD"]
TO_EMAIL       = os.environ["TO_EMAIL"]
NEWS_RSS_URL   = os.environ["NEWS_RSS_URL"]

# ============================================================
#  FETCH HEADLINES FROM RSS
# ============================================================

def fetch_ai_news():
    response = requests.get(NEWS_RSS_URL, timeout=10)
    root = ET.fromstring(response.content)
    items = root.findall(".//item")[:15]

    headlines = ""
    links = {}
    articles_text = {}

    for i, item in enumerate(items, 1):
        title  = item.findtext("title", "No title")
        link   = item.findtext("link", "")
        source = item.findtext("source", "Unknown")

        headlines += f"{i}. {title} ({source})\n"
        links[i] = (title, link, source)

        # fetch full article text
        print(f"Fetching article {i}/15: {title[:50]}...")
        articles_text[i] = fetch_article_text(link)

    print(f"Fetched {len(items)} headlines and articles")
    return headlines, links, articles_text

# ============================================================
#  FETCH FULL ARTICLE
# ============================================================

def fetch_article_text(url, max_chars=3000):
    try:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; NewsBot/1.0)"}
        response = requests.get(url, timeout=8, headers=headers)
        soup = BeautifulSoup(response.text, "lxml")

        for tag in soup(["script", "style", "nav", "footer", "header",
                          "aside", "form", "iframe"]):
            tag.decompose()

        text = soup.get_text(separator=" ", strip=True)

        text = re.sub(r"\s+", " ", text).strip()

        return text[:max_chars]

    except Exception as e:
        print(f"Could not fetch article: {e}")
        return ""

# ============================================================
#  GEMINI SUMMARY
# ============================================================

def summarize_with_gemini(headlines, articles_text):
    client = genai.Client(api_key=GEMINI_API_KEY)

    # build enriched headlines with article content
    enriched = ""
    for i, line in enumerate(headlines.strip().split("\n"), 1):
        enriched += f"\n{line}\n"
        content = articles_text.get(i, "")
        if content:
            enriched += f"   Article content: {content}\n"
        else:
            enriched += f"   Article content: (not available)\n"

    prompt = f"""You are an expert AI news curator. I will give you numbered headlines,
                 each followed by the actual article content.
 
                 IMPORTANT: Respond ONLY with a valid JSON array. No markdown, no code fences, no explanation,
                 no trailing commas, no comments. Pure raw JSON only.
 
                 Format:
                 [
                 {{
                     "number": <integer, the headline number from the list>,
                     "title": "<original title>",
                     "source": "<source name>",
                     "summary": "<3 sentences summarising the story using the article content, not just the headline>",
                     "why_matters": "<1 sentence explaining why this matters to the AI field>",
                     "key_detail": "<1 concrete specific detail from the article that most people would miss>"
                 }}
                 ]
 
                 Pick the 5 most important stories. Use the actual article content to write deep, specific summaries.
                 Avoid vague summaries — include real names, numbers, and facts from the article when available.
 
                 Then add this object at the end of the array:
                 {{
                 "number": 0,
                 "title": "Big Picture",
                 "source": "",
                 "summary": "<2 sentences on the overall AI trend today based on all the articles>",
                 "why_matters": "",
                 "key_detail": ""
                 }}
 
                 Headlines and articles:
                 {enriched}
                 """

    response = client.models.generate_content(
        model="gemini-3.1-flash-lite",
        contents=prompt
    )
    print("✅ Digest generated")
    return response.text

# ============================================================
#  JSON PARSER
# ============================================================

def parse_gemini_json(raw_text):
    
    clean = re.sub(r"```json|```", "", raw_text).strip()

    try:
        return json.loads(clean)
    except json.JSONDecodeError:
        pass

    match = re.search(r"\[.*\]", clean, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    fixed = re.sub(r",\s*([}\]])", r"\1", clean)
    try:
        return json.loads(fixed)
    except json.JSONDecodeError:
        pass

    print("Could not parse Gemini JSON. Sending fallback email.")

    return [
        {
            "number": 0,
            "title": "Big Picture",
            "source": "",
            "summary": "Gemini returned an unexpected format today. Please check the GitHub Actions log for the raw output.",
            "why_matters": ""
        }
    ]

# ============================================================
#  BUILD HTML AND EMAIL
# ============================================================

def build_html_email(digest_json_text, links):
    stories = parse_gemini_json(digest_json_text)
    today   = date.today().strftime("%B %d, %Y")

    html = f"""
            <!DOCTYPE html>
            <html>
            <head>
            <meta charset="UTF-8">
            <style>
            body       {{ font-family: Arial, sans-serif; background: #f4f6f9; margin: 0; padding: 20px; }}
            .card      {{ background: white; border-radius: 10px; padding: 30px;
                            max-width: 680px; margin: 0 auto;
                            box-shadow: 0 2px 8px rgba(0,0,0,0.08); }}
            h1         {{ color: #1a1a2e; font-size: 22px; margin-bottom: 4px; }}
            .date      {{ color: #888; font-size: 13px; margin-bottom: 28px; }}
            .story     {{ border-left: 4px solid #4f8ef7; padding: 14px 16px;
                            margin-bottom: 20px; background: #f9fbff;
                            border-radius: 0 8px 8px 0; }}
            .story h2  {{ font-size: 15px; color: #1a1a2e; margin: 0 0 8px 0; }}
            .story a   {{ color: #4f8ef7; text-decoration: none; }}
            .story a:hover {{ text-decoration: underline; }}
            .summary   {{ color: #444; font-size: 14px; margin: 0 0 6px 0; }}
            .matters   {{ color: #e07b00; font-size: 13px; font-weight: bold; margin: 0 0 4px 0; }}
            .detail    {{ color: #2a7a2a; font-size: 13px; font-style: italic; margin: 0 0 4px 0; }}
            .source    {{ color: #aaa; font-size: 12px; margin-top: 6px; }}
            .bigpic    {{ background: #1a1a2e; color: white; border-radius: 8px;
                            padding: 18px 20px; margin-top: 28px; }}
            .bigpic h2 {{ margin: 0 0 8px 0; font-size: 15px; color: #4f8ef7; }}
            .bigpic p  {{ margin: 0; font-size: 14px; color: #ddd; }}
            .footer    {{ text-align: center; color: #bbb; font-size: 12px; margin-top: 24px; }}
            </style>
            </head>
            <body>
            <div class="card">
            <h1>🤖 Daily AI News Digest</h1>
            <div class="date">{today} &nbsp;·&nbsp; Top 5 stories curated by Gemini</div>
            """

    story_num = 0
    for s in stories:
        if s["number"] == 0:
            html += f"""
                     <div class="bigpic">
                         <h2>🌐 Big Picture</h2>
                         <p>{s["summary"]}</p>
                     </div>
                     """
        else:
            story_num += 1
            num        = s["number"]
            link       = links.get(num, ("", "#", ""))[1]
            source     = s.get("source", "")
            key_detail = s.get("key_detail", "")

            html += f"""
                     <div class="story">
                         <h2>{story_num}. <a href="{link}" target="_blank">{s["title"]}</a></h2>
                         <p class="summary">{s["summary"]}</p>
                         <p class="matters">💡 Why it matters: {s["why_matters"]}</p>
                         {"<p class='detail'>🔍 Key detail: " + key_detail + "</p>" if key_detail else ""}
                         <p class="source">📰 {source}</p>
                     </div>
                     """

    html += """
            <div class="footer">
                📡 Source: Google News RSS &nbsp;·&nbsp; 🤖 Summarized by Gemini 2.0 Flash
            </div>
            </div>
            </body>
            </html>
            """
    return html

# ============================================================
#  EMAIL SENDING
# ============================================================

def send_email(html_content):
    today = date.today().strftime("%B %d, %Y")
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Daily AI News Digest — {today}"
    msg["From"]    = GMAIL_USER
    msg["To"]      = TO_EMAIL
    msg.attach(MIMEText(html_content, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_USER, GMAIL_PASSWORD)
        server.sendmail(GMAIL_USER, TO_EMAIL, msg.as_string())
    print("Email sent!")

# ============================================================
#  MAIN EXECUTION
# ============================================================
if __name__ == "__main__":
    print("1) Fetching headlines...")
    headlines, links, articles_text = fetch_ai_news()

    print("2) Summarising with Gemini...")
    digest_json = summarize_with_gemini(headlines, articles_text)
    print("Raw Gemini output:", digest_json[:300])

    print("3) Building HTML email...")
    html = build_html_email(digest_json, links)

    print("4) Sending email...")
    send_email(html)
    print("Done!")