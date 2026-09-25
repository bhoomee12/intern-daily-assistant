import os, json
from dotenv import load_dotenv
from google import genai

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def triage_email(email):
    prompt = f"""Classify this email into exactly one category: 
"reply_needed", "fyi", or "waiting_on_other".
Respond with ONLY the category word, nothing else.

Subject: {email['subject']}
Body: {email['body']}"""

    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=prompt
    )
    return response.text.strip()

with open("data/emails.json") as f:
    emails = json.load(f)

for email in emails:
    category = triage_email(email)
    print(f"[{category}] {email['subject']}")