import streamlit as st
import smtplib
import time
import concurrent.futures
import uuid
import random
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr, make_msgid

# --- Page Config (Pehle Jaisa) ---
st.set_page_config(page_title="Radhe Radhe Mailer", layout="wide")

# --- CSS (Pehle Jaisa Design) ---
st.markdown("""
    <style>
    .stApp { background-color: #f0f2f6; }
    .main-card {
        background-color: white; padding: 30px; border-radius: 15px;
        box-shadow: 0px 4px 20px rgba(0,0,0,0.1);
        max-width: 950px; margin: auto; border: 1px solid #e0e4e9;
    }
    input, textarea { color: #000000 !important; font-weight: 500 !important; background-color: #ffffff !important; }
    label p { color: #333333 !important; font-weight: bold !important; }
    div.stButton > button:first-child {
        width: 100%; height: 70px; background-color: #4285F4 !important;
        color: white !important; font-size: 20px !important; font-weight: bold;
        border-radius: 10px; border: none;
    }
    header, footer {visibility: hidden;}
    [data-testid="stHeader"] {display: none;}
    </style>
""", unsafe_allow_html=True)

# --- Pro Inbox Logic ---
def sanitize_content(text):
    # Spam words rotation for safety
    synonyms = {
        r"error": ["issue", "anomaly", "glitch", "technical gap"],
        r"search results": ["SERP indexing", "organic visibility", "web presence"],
        r"screenshot": ["visual report", "scan copy", "documentation"],
    }
    for word, replacements in synonyms.items():
        text = re.sub(word, random.choice(replacements), text, flags=re.IGNORECASE)
    
    unique_ref = f""
    return f"<html><body style='font-family: Arial;'>{text.replace('\n', '<br>')}{unique_ref}</body></html>"

# --- High-Speed Safe Worker ---
def send_engine_pro(target, job):
    try:
        # Rotation Logic
        bodies = [b for b in [job['b1'], job['b2'], job['b3']] if b.strip()]
        final_body = random.choice(bodies) if bodies else job['b1']

        msg = MIMEMultipart('alternative')
        msg['Subject'] = job['s']
        msg['From'] = formataddr((job['n'], job['e']))
        msg['To'] = target
        msg['Message-ID'] = make_msgid(domain='gmail.com')
        msg['X-Mailer'] = "Microsoft Outlook 16.0"
        
        msg.attach(MIMEText(sanitize_content(final_body), 'html'))

        with smtplib.SMTP('smtp.gmail.com', 587, timeout=12) as server:
            server.starttls()
            server.login(job['e'], job['p'])
            time.sleep(random.uniform(0.7, 2.0)) # Safety Delay
            server.send_message(msg)
        return True
    except:
        return False

# --- Session Management ---
if 'auth' not in st.session_state: st.session_state.auth = False
if 'is_sending' not in st.session_state: st.session_state.is_sending = False
if 'job_task' not in st.session_state: st.session_state.job_task = None

# --- UI ---
if not st.session_state.auth:
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
    if st.button("LOGIN"):
        if u == "YATENDRA LODHI" and p == "YATENDRA LODHI":
            st.session_state.auth = True
            st.rerun()
else:
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center;'>📧 Fast Mail Launcher</h2>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1: s_name = st.text_input("Sender Name", key="sn")
    with col2: s_email = st.text_input("Your Gmail", key="se")
    
    col3, col4 = st.columns(2)
    with col3: s_pass = st.text_input("App Password", type="password", key="sp")
    with col4: subject = st.text_input("Subject", key="sub")
    
    st.write("**Body Templates (Pattern Rotation Active)**")
    t1, t2, t3 = st.columns(3)
    with t1: b1 = st.text_area("Template A", height=150, key="b1")
    with t2: b2 = st.text_area("Template B", height=150, key="b2")
    with t3: b3 = st.text_area("Template C", height=150, key="b3")
    
    recipients_raw = st.text_area("Recipients", height=120, key="rec")

    if st.session_state.is_sending:
        st.button("⌛ Sending Parallel Batch...", disabled=True)
        job = st.session_state.job_task
        p_bar = st.progress(0)
        success = 0
        
        

        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = {executor.submit(send_engine_pro, em, job): em for em in job['r']}
            for i, f in enumerate(concurrent.futures.as_completed(futures)):
                if f.result() is True: success += 1
                p_bar.progress((i + 1) / len(job['r']))
        
        st.session_state.is_sending = False
        st.session_state.job_task = None
        st.success(f"✅ Kaam Ho Gaya! {success} mails reached Inbox.")
        st.balloons()
        time.sleep(2)
        st.rerun()
            
    else:
        btn_col, logout_col = st.columns([0.8, 0.2])
        with btn_col:
            if st.button("Send All"):
                unique_emails = list(dict.fromkeys([e.strip() for e in recipients_raw.replace(',', '\n').split('\n') if e.strip()]))
                if s_email and s_pass and unique_emails:
                    st.session_state.job_task = {'n': s_name, 'e': s_email, 'p': s_pass, 's': subject, 'b1': b1, 'b2': b2, 'b3': b3, 'r': unique_emails}
                    st.session_state.is_sending = True
                    st.rerun()
        with logout_col:
            if st.button("Logout"):
                st.session_state.auth = False
                st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)
