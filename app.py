import streamlit as st
import smtplib
import time
import concurrent.futures
import re
import uuid
import random
import string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr, make_msgid

# --- Page Config & UI ---
st.set_page_config(page_title="Ultra Safe Mailer", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    .main-card {
        background-color: white; padding: 35px; border-radius: 15px;
        box-shadow: 0px 4px 20px rgba(0,0,0,0.08);
        max-width: 1000px; margin: auto; border: 1px solid #e9ecef;
    }
    header, footer {visibility: hidden;}
    [data-testid="stHeader"] {display: none;}
    div.stButton > button {
        width: 100%; height: 60px; background-color: #1a73e8 !important;
        font-weight: bold; border-radius: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# --- Pro Anti-Spam Engine ---
def ultra_safe_sanitizer(text):
    # Professional English Synonyms to bypass AI filters
    replacements = {
        r"free": "zero-cost", r"win": "receive", r"money": "capital",
        r"cash": "funds", r"urgent": "time-sensitive", r"offer": "proposal",
        r"click": "follow", r"buy": "purchase", r"gift": "bonus"
    }
    for pattern, replacement in replacements.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    
    # Adding a hidden random fingerprint at the end (Inbox Booster)
    fingerprint = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
    hidden_html = f"<div style='display:none; color:white; font-size:0px;'>Ref-{fingerprint}-{uuid.uuid4()}</div>"
    
    return text.replace('\n', '<br>') + hidden_html

# --- Session Management ---
if 'auth' not in st.session_state: st.session_state.auth = False
if 'sending' not in st.session_state: st.session_state.sending = False
if 'limit_logs' not in st.session_state: st.session_state.limit_logs = {}

# --- Login ---
if not st.session_state.auth:
    _, col, _ = st.columns([1, 1.5, 1])
    with col:
        st.write("### 🔐 Console Access")
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Unlock"):
            if u == "@#2026@#" and p == "@#2026@#":
                st.session_state.auth = True
                st.rerun()
else:
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>🚀 Ultra-Safe Turbo Mailer</h3>", unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    with c1: s_name = st.text_input("Sender Name", key="sn")
    with c2: s_email = st.text_input("Your Gmail", key="se")
    
    c3, c4 = st.columns(2)
    with c3: s_pass = st.text_input("App Password", type="password", key="sp")
    with c4: subject = st.text_input("Subject", key="sub")
    
    c5, c6 = st.columns(2)
    with c5: body_input = st.text_area("Message Template", height=200, key="msg")
    with c6: rec_raw = st.text_area("Recipients List", height=200, key="rec")

    # --- Worker Engine ---
    def safe_send_worker(target):
        try:
            msg = MIMEMultipart()
            msg['Subject'] = subject
            msg['From'] = formataddr((s_name, s_email))
            msg['To'] = target
            msg['Message-ID'] = make_msgid()
            msg['X-Mailer'] = "Microsoft Outlook 16.0" # Impersonating professional software
            
            clean_html = f"<html><body>{ultra_safe_sanitizer(body_input)}</body></html>"
            msg.attach(MIMEText(clean_html, 'html'))

            with smtplib.SMTP('smtp.gmail.com', 587, timeout=12) as server:
                server.starttls()
                server.login(s_email, s_pass)
                server.send_message(msg)
            
            st.session_state.limit_logs[s_email].append(time.time())
            return True, target
        except smtplib.SMTPAuthenticationError:
            return "AUTH_ERROR", "App Password wrong"
        except Exception as e:
            return False, str(e)

    # --- Control ---
    if st.session_state.sending:
        st.button("⌛ Sending... (Locked)", disabled=True)
    else:
        if st.button("Send All"):
            emails = [e.strip() for e in rec_raw.replace(',', '\n').split('\n') if e.strip()]
            now = time.time()
            if s_email not in st.session_state.limit_logs: st.session_state.limit_logs[s_email] = []
            st.session_state.limit_logs[s_email] = [t for t in st.session_state.limit_logs[s_email] if now - t < 3600]

            if len(st.session_state.limit_logs[s_email]) >= 28:
                st.error(f"❌ Limit Reached (28/hr) for {s_email}")
            elif not s_email or not s_pass or not emails:
                st.warning("Details missing!")
            else:
                st.session_state.sending = True
                st.session_state.targets = emails
                st.rerun()

    # --- Turbo Parallel Processing ---
    if st.session_state.sending:
        targets = st.session_state.targets
        p_bar = st.progress(0)
        status = st.empty()
        success = 0
        
        

        # 3 Parallel Workers (Max Speed safely)
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = {executor.submit(safe_send_worker, em): em for em in targets}
            for i, f in enumerate(concurrent.futures.as_completed(futures)):
                res, info = f.result()
                
                if res == "AUTH_ERROR":
                    st.error("❌ App Password wrong! ❌")
                    st.session_state.sending = False
                    st.stop()
                
                if res is True: success += 1
                p_bar.progress((i + 1) / len(targets))
                status.info(f"📊 Progress: {i+1}/{len(targets)} | Successfully Inboxed: {success}")

        st.session_state.sending = False
        st.success(f"Task Finished! {success} Delivered.")
        st.balloons()
        time.sleep(2)
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)
