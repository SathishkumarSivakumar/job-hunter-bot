import os
import time
import random
import hashlib
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import requests

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_APP_PASS = os.getenv("GMAIL_APP_PASS")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

DB_HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

def send_telegram(msg: str):
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=10)

def get_candidate_profile():
    url = f"{SUPABASE_URL}/rest/v1/master_profile?select=*&limit=1"
    res = requests.get(url, headers=DB_HEADERS, timeout=15)
    return res.json()[0] if res.status_code == 200 and res.json() else None

def is_duplicate(job_hash: str) -> bool:
    url = f"{SUPABASE_URL}/rest/v1/application_history?job_hash=eq.{job_hash}&select=id"
    res = requests.get(url, headers=DB_HEADERS, timeout=15)
    return len(res.json()) > 0 if res.status_code == 200 else False

def record_dispatch(company: str, role: str, email: str, job_hash: str):
    url = f"{SUPABASE_URL}/rest/v1/application_history"
    data = {"company_name": company, "role_title": role, "portal_or_email": email, "job_hash": job_hash, "status": "DISPATCHED"}
    requests.post(url, headers=DB_HEADERS, json=data, timeout=15)

def send_tailored_pitch(company: str, role: str, recipient_email: str, profile: dict) -> bool:
    subject = f"Application: {role} | {profile['full_name']} (Immediate Joiner - 0 Days Notice)"
    body = f"""Hi Talent Acquisition Team at {company},

I am writing to express my strong interest in data & business intelligence opportunities ({role}) at {company}.

Candidate Highlights:
• Experience: 1 Year as Data & MIS Analyst Intern at RR IT Solutions, building business reporting pipelines and analytics models.
• Core Tech Stack: SQL (CTEs, Window Functions, Normalization), Power BI (DAX, Star Schema), Advanced Excel (XLOOKUP, Pivot), and Python.
• Project Delivery:
  - TATA CLiQ BI Analytics: Built end-to-end Star Schema tracking revenue, profit margins, and retention.
  - Apollo Care Hospital DB: Engineered relational schemas, constraints, and optimized queries.
  - Reliance Trends Sales Dashboard: Performed store and category sales analysis in Excel.
  - Deep Learning: Trained CNN age detection models using TensorFlow and OpenCV.
• Education: B.E in EEE (Kongunadu College of Engineering and Technology, CGPA: 8.3/10, 2024 Graduate).
• Notice Period: 0 Days (Immediate Joiner).
• Preferred Locations: Chennai, Bengaluru, Coimbatore, Hyderabad, or Remote.

Contact:
Phone: {profile['phone']}
Email: {profile['email']}
Current City: {profile['current_city']}

I look forward to discussing how my analytical experience can add immediate value to your current projects.

Best regards,
{profile['full_name']}
"""
    msg = MIMEMultipart()
    msg['From'] = GMAIL_USER
    msg['To'] = recipient_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(GMAIL_USER, GMAIL_APP_PASS)
            server.sendmail(GMAIL_USER, recipient_email, msg.as_string())
        return True
    except Exception as e:
        print(f"[-] Dispatch error to {company}: {e}")
        return False

TARGET_COMPANIES = [
    {"name": "Tata Consultancy Services (TCS)", "role": "Data Analyst / Python Specialist", "email": "careers@tcs.com"},
    {"name": "Zoho Corporation", "role": "Business Intelligence & Analytics Specialist", "email": "recruit@zohocorp.com"},
    {"name": "Cognizant Technology Solutions", "role": "Power BI & SQL Developer", "email": "careersindia@cognizant.com"},
    {"name": "Accenture India", "role": "Data Engineering & Analytics Associate", "email": "india.recruitment@accenture.com"},
    {"name": "Freshworks", "role": "Analytics & Automation Engineer", "email": "careers@freshworks.com"},
    {"name": "Walmart Global Tech", "role": "Associate Data Analyst", "email": "india-talent@walmart.com"},
    {"name": "HCLTech", "role": "SQL & Data Pipeline Specialist", "email": "indiacareers@hcl.com"},
    {"name": "LTIMindtree", "role": "Power BI & BI Developer", "email": "careers@ltimindtree.com"},
    {"name": "Wipro Technologies", "role": "Data Analyst - Retail & Sales", "email": "manager.campus@wipro.com"},
    {"name": "Infosys", "role": "Business Intelligence Analyst", "email": "careers_india@infosys.com"}
]

def main():
    profile = get_candidate_profile()
    if not profile:
        print("[-] Profile missing.")
        return

    dispatched = []
    for target in TARGET_COMPANIES:
        job_key = f"{target['name']}_{target['role']}_{target['email']}".lower()
        job_hash = hashlib.sha256(job_key.encode()).hexdigest()[:16]

        if is_duplicate(job_hash):
            continue

        if send_tailored_pitch(target["name"], target["role"], target["email"], profile):
            record_dispatch(target["name"], target["role"], target["email"], job_hash)
            dispatched.append(f"✅ *{target['name']}* — {target['role']}")

        time.sleep(random.uniform(25.0, 40.0))

    if dispatched:
        msg = f"🚀 *Job Hunter Report (9 AM – 12 PM)*\n\n👤 *{profile['full_name']}* (CGPA: 8.3 | 0-Day Notice)\n\n" + "\n".join(dispatched)
    else:
        msg = "ℹ️ இன்றைய டார்கெட் நிறுவனங்களுக்கு ஏற்கனவே அனுப்பப்பட்டுவிட்டது."
    send_telegram(msg)

if __name__ == "__main__":
    main()
