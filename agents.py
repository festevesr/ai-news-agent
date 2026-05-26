# ============================================================
#  IMPORT LIBRARIES
# ============================================================

import os
import requests
import smtplib
import xml.etree.ElementTree as ET
import google.generativeai as genai
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
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
    for i, item in enumerate(items, 1):
        title  = item.findtext("title", "No title")
        link   = item.findtext("link", "")
        source = item.findtext("source", "Unknown")
        headlines += f"{i}. {title} ({source})\n"
        links[i] = (title, link, source)
    return headlines, links

# ============================================================
#  GEMINI SUMMARY
# ============================================================

def summarize_with_gemini(headlines):
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-2.5-flash")

    prompt = f"""You are an expert AI news curator. I will give you numbered headlines.

                 Your task — respond ONLY with a JSON array, no markdown, no explanation, just raw JSON:
                [
                {{
                    "number": <headline number 1-15>,
                    "title": "<original title>",
                    "source": "<source name>",
                    "summary": "<2 sentences summarising the story>",
                    "why_matters": "<1 sentence explaining why this matters>"
                }},
                ...
                ]

                Pick the 5 most important stories. Use the exact headline number from the list.

                Headlines:
                {headlines}

                Also add one final object at the end:
                {{
                "number": 0,
                "title": "Big Picture",
                "source": "",
                "summary": "<2 sentences on the overall AI trend today>",
                "why_matters": ""
                }}
                """
    
    response = model.generate_content(prompt)
    return response.text

# ============================================================
#  BUILD HTML AND EMAIL
# ============================================================

def build_html_email(digest_json, links):
    import json, re

    # strip any accidental markdown fences
    clean = re.sub(r"```json|```", "", digest_json).strip()
    stories = json.loads(clean)

    today = date.today().strftime("%B %d, %Y")

    html = f"""
            <!DOCTYPE html>
            <html>
            <head>
            <meta charset="UTF-8">
            <style>
            body      {{ font-family: Arial, sans-serif; background: #f4f6f9; margin: 0; padding: 20px; }}
            .card     {{ background: white; border-radius: 10px; padding: 30px;
                        max-width: 680px; margin: 0 auto;
                        box-shadow: 0 2px 8px rgba(0,0,0,0.08); }}
            h1        {{ color: #1a1a2e; font-size: 22px; margin-bottom: 4px; }}
            .date     {{ color: #888; font-size: 13px; margin-bottom: 28px; }}
            .story    {{ border-left: 4px solid #4f8ef7; padding: 14px 16px;
                        margin-bottom: 20px; background: #f9fbff;
                        border-radius: 0 8px 8px 0; }}
            .story h2 {{ font-size: 15px; color: #1a1a2e; margin: 0 0 8px 0; }}
            .story a  {{ color: #4f8ef7; text-decoration: none; }}
            .story a:hover {{ text-decoration: underline; }}
            .summary  {{ color: #444; font-size: 14px; margin: 0 0 6px 0; }}
            .matters  {{ color: #e07b00; font-size: 13px; font-weight: bold; }}
            .source   {{ color: #aaa; font-size: 12px; margin-top: 6px; }}
            .bigpic   {{ background: #1a1a2e; color: white; border-radius: 8px;
                        padding: 18px 20px; margin-top: 28px; }}
            .bigpic h2 {{ margin: 0 0 8px 0; font-size: 15px; color: #4f8ef7; }}
            .bigpic p  {{ margin: 0; font-size: 14px; color: #ddd; }}
            .footer   {{ text-align: center; color: #bbb; font-size: 12px; margin-top: 24px; }}
            </style>
            </head>
            <body>
            <div class="card">
            <h1>Daily AI News Digest</h1>
            <div class="date">{today} &nbsp;·&nbsp; Top 5 stories curated by Gemini</div>
            """

    story_num = 0

    for s in stories:
        if s["number"] == 0:
            html += f"""
                     <div class="bigpic">
                         <h2>Big Picture</h2>
                         <p>{s["summary"]}</p>
                     </div>
                     """
        else:
            story_num += 1
            num    = s["number"]
            title  = s["title"]
            link   = links.get(num, ("", "", ""))[1] if num in links else "#"
            source = s.get("source", "")

            html += f"""
                     <div class="story">
                         <h2>{story_num}. <a href="{link}" target="_blank">{title}</a></h2>
                         <p class="summary">{s["summary"]}</p>
                         <p class="matters">💡 Why it matters: {s["why_matters"]}</p>
                         <p class="source">📰 {source}</p>
                     </div>
                     """

    html += """
            <div class="footer">
                Source: Google News RSS &nbsp;·&nbsp; Summarized by Gemini 2.0 Flash
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
    print("✅ Email sent!")

# ============================================================
#  MAIN EXECUTIO
# ============================================================
if __name__ == "__main__":
    print("1) Fetching headlines...")
    headlines, links = fetch_ai_news()

    print("2) Summarising with Gemini...")
    digest_json = summarize_with_gemini(headlines)

    print("3) Building HTML email...")
    html = build_html_email(digest_json, links)

    print("4) Sending email...")
    send_email(html)
    print("Done!")