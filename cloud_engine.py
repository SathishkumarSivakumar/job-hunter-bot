import os
import sys
import time
import random
import hashlib
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import requests

# Secrets load pannudhal
SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip().rstrip("/")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "").strip()
GMAIL_USER = os.getenv("GMAIL_USER", "").strip()
GMAIL_APP_PASS = os.getenv("GMAIL_APP_PASS", "").strip().replace(" ", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()

DB_HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

def send_telegram(msg: str):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"[-] Telegram dispatch error: {e}")

def get_candidate_profile():
    # URL formatting error varama irukka direct strip
    base_url = SUPABASE_URL.rstrip('/')
    endpoint = f"{base_url}/rest/v1/master_profile?select=*"
    try:
        res = requests.get(endpoint, headers=DB_HEADERS, timeout=15)
        if res.status_code == 200:
            data = res.json()
            if data and len(data) > 0:
                return data[0]
            print("[-] Supabase master_profile table empty-aa irukku.")
        else:
            print(f"[-] Supabase Error: {res.status_code} - {res.text}")
    except Exception as e:
        print(f"[-] Supabase connection error: {e}")
    return None

def is_duplicate(job_hash: str) -> bool:
    base_url = SUPABASE_URL.rstrip('/')
    endpoint = f"{base_url}/rest/v1/application_history?job_hash=eq.{job_hash}&select=id"
    try:
        res = requests.get(endpoint, headers=DB_HEADERS, timeout=15)
        if res.status_code == 200:
            return len(res.json()) > 0
    except Exception:
        pass
    return False

def record_dispatch(company: str, role: str, email: str, job_hash: str):
    base_url = SUPABASE_URL.rstrip('/')
    endpoint = f"{base_url}/rest/v1/application_history"
    data = {
        "company_name": company,
        "role_title": role,
        "portal_or_email": email,
        "job_hash": job_hash,
        "status": "DISPATCHED"
    }
    try:
        requests.post(endpoint, headers=DB_HEADERS, json=data, timeout=15)
    except Exception as e:
        print(f"[-] History log error: {e}")

def send_tailored_pitch(company: str, role: str, recipient_email: str, profile: dict) -> bool:
    if not GMAIL_USER or not GMAIL_APP_PASS:
        return False

    name = profile.get('full_name', 'Sathishkumar S')
    phone = profile.get('phone', '+91 9789704124')
    email = profile.get('email', 'kumar109662@gmail.com')
    city = profile.get('current_city', 'Chennai, India')

    subject = f"Application: {role} | {name} (Immediate Joiner - 0 Days Notice)"
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
Phone: {phone}
Email: {email}
Current City: {city}

I look forward to discussing how my analytical experience can add immediate value to your current projects.

Best regards,
{name}
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
        print(f"[✓] Sent email to {company} ({recipient_email})")
        return True
    except Exception as e:
        print(f"[-] SMTP Dispatch error to {company}: {e}")
        return False

TARGET_COMPANIES = [
    {"name": "Tata Consultancy Services (TCS)", "role": "Data Analyst / Python Specialist", "email": "careers@tcs.com"},
    {"name": "Zoho Corporation", "role": "Business Intelligence & Analytics Specialist", "email": "recruit@zohocorp.com"},
    {"name": "Cognizant Technology Solutions", "role": "Power BI & SQL Developer", "email": "careersindia@cognizant.com"},
    {"name": "Accenture India", "role": "Data Engineering & Analytics Associate", "email": "india.recruitment@accenture.com"},
    {"name": "Freshworks", "role": "Analytics & Automation Engineer", "email": "careers@freshworks.com"}
]

def main():
    profile = get_candidate_profile()
    if not profile:
        print("[!] Stopping: Candidate profile Supabase-la load aagala.")
        sys.exit(1)

    print(f"[*] Dispatching for: {profile.get('full_name')}")
    dispatched = []

    for target in TARGET_COMPANIES:
        job_key = f"{target['name']}_{target['role']}_{target['email']}".lower()
        job_hash = hashlib.sha256(job_key.encode()).hexdigest()[:16]

        if is_duplicate(job_hash):
            print(f"[~] Already applied to {target['name']}. Skipping.")
            continue

        if send_tailored_pitch(target["name"], target["role"], target["email"], profile):
            record_dispatch(target["name"], target["role"], target["email"], job_hash)
            dispatched.append(f"✅ *{target['name']}* — {target['role']}")

        delay = random.uniform(20.0, 30.0)
        print(f"[*] Sleeping {delay:.1f}s before next application...")
        time.sleep(delay)

    if dispatched:
        msg = f"🚀 *Job Hunter Report (9 AM – 12 PM)*\n\n👤 *{profile.get('full_name')}* (CGPA: 8.3 | 0-Day Notice)\n\n" + "\n".join(dispatched)
    else:
        msg = "ℹ️ Target companies-ku profile already send aayiduchu."
    
    send_telegram(msg)
    print("[*] Engine completed successfully.")

if __name__ == "__main__":
    main()
