import streamlit as st
import smtplib
import time
import concurrent.futures
import re
import uuid
import random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr, make_msgid

# --- Page Config ---
st.set_page_config(page_title="Pro Mailer Console", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #f4f7f6; }
    .main-card {
        background-color: white; padding: 35px; border-radius: 15px;
        box-shadow: 0px 8px 25px rgba(0,0,0,0.1);
        max-width: 1000px; margin: auto; border: 1px solid #e1e4e8;
    }
    header, footer {visibility: hidden;}
    [data-testid="stHeader"] {display: none;}
    div.stButton > button {
        width: 100%; height: 60px; background-color: #28a745 !important;
        font-weight: bold; border-radius: 10px; color: white !important; font-size: 18px;
    }
    input, textarea { border: 1px solid #ced4da !important; }
    </style>
""", unsafe_allow_html=True)

# --- Anti-Spam Synonym Logic ---
def bypass_spam_filter(text):
    synonyms = {
        r"free": "complimentary", r"win": "attain", r"money": "funds",
        r"urgent": "priority", r"click": "access", r"offer": "opportunity",
        r"cash": "revenue", r"buy": "secure"
    }
    safe_text = text
    for p, r in synonyms.items():
        safe_text = re.sub(p, r, safe_text, flags=re.IGNORECASE)
    
    # Invisible unique tag for inboxing
    unique_tag = f"<div style='display:none;'>Ref-{uuid.uuid4()}</div>"
    return safe_text.replace('\n', '<br>') + unique_tag

# --- Session Management ---
if 'auth' not in st.session_state: st.session_state.auth = False
if 'sending_active' not in st.session_state: st.session_state.sending_active = False
if 'job_snapshot' not in st.session_state: st.session_state.job_snapshot = None
if 'hourly_logs' not in st.session_state: st.session_state.hourly_logs = {}

# --- Login ---
if not st.session_state.auth:
    _, col, _ = st.columns([1, 1.5, 1])
    with col:
        st.write("### 🔐 Secure Login")
        u = st.text_input("User")
        p = st.text_input("Pass", type="password")
        if st.button("Unlock System"):
            if u == "@#2026@#" and p == "@#2026@#":
                st.session_state.auth = True
                st.rerun()
else:
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>🚀 Turbo Inbox Launcher</h3>", unsafe_allow_html=True)
    
    # Ye inputs hamesha editable rahenge, sending ke waqt bhi
    c1, c2 = st.columns(2)
    with c1: ui_name = st.text_input("Sender Name", key="ui_n")
    with c2: ui_email = st.text_input("Your Gmail ID", key="ui_e")
    
    c3, c4 = st.columns(2)
    with c3: ui_pass = st.text_input("App Password", type="password", key="ui_p")
    with c4: ui_sub = st.text_input("Email Subject", key="ui_s")
    
    c5, c6 = st.columns(2)
    with c5: ui_body = st.text_area("Message Body", height=180, key="ui_b")
    with c6: ui_rec = st.text_area("Recipients", height=180, key="ui_r")

    # --- SMTP Turbo Worker ---
    def background_worker(target_email, frozen_job):
        try:
            msg = MIMEMultipart()
            msg['Subject'] = frozen_job['sub']
            msg['From'] = formataddr((frozen_job['name'], frozen_job['email']))
            msg['To'] = target_email
            msg['Message-ID'] = make_msgid()
            msg['X-Mailer'] = "Outlook/16.0" # Inbox trust booster
            
            clean_html = f"<html><body>{bypass_spam_filter(frozen_job['body'])}</body></html>"
            msg.attach(MIMEText(clean_html, 'html'))

            with smtplib.SMTP('smtp.gmail.com', 587, timeout=12) as server:
                server.starttls()
                server.login(frozen_job['email'], frozen_job['pass'])
                server.send_message(msg)
            
            st.session_state.hourly_logs[frozen_job['email']].append(time.time())
            return True, target_email
        except smtplib.SMTPAuthenticationError:
            return "AUTH_ERROR", "App Password Galat Hai"
        except Exception as e:
            return False, str(e)

    # --- Control Logic ---
    st.write("")
    if st.session_state.sending_active:
        st.warning(f"⏳ Sending in progress from: {st.session_state.job_snapshot['email']}")
        st.button("⚙️ BATCH RUNNING (UI IS UNLOCKED)...", disabled=True)
    else:
        if st.button("🚀 Send All"):
            targets = [e.strip() for e in ui_rec.replace(',', '\n').split('\n') if e.strip()]
            
            # Auto Reset logs after 1 hour
            now = time.time()
            if ui_email not in st.session_state.hourly_logs: st.session_state.hourly_logs[ui_email] = []
            st.session_state.hourly_logs[ui_email] = [t for t in st.session_state.hourly_logs[ui_email] if now - t < 3600]

            if not ui_email or not ui_pass or not targets:
                st.error("Details fill karo!")
            else:
                # FREEZE: Saara data snapshot mein save kar liya
                st.session_state.job_snapshot = {
                    'name': ui_name, 'email': ui_email, 'pass': ui_pass,
                    'sub': ui_sub, 'body': ui_body, 'targets': targets
                }
                st.session_state.sending_active = True
                st.rerun()

    # --- The Parallel Execution Engine ---
    if st.session_state.sending_active and st.session_state.job_snapshot:
        job = st.session_state.job_snapshot
        p_bar = st.progress(0)
        status = st.empty()
        success = 0
        
        # 3 Parallel Workers for Fast Delivery
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = {executor.submit(background_worker, em, job): em for em in job['targets']}
            for i, f in enumerate(concurrent.futures.as_completed(futures)):
                res, detail = f.result()
                
                if res == "AUTH_ERROR":
                    st.error(f"❌ Login Failed for {job['email']}. Password check karein.")
                    st.session_state.sending_active = False
                    st.stop()
                
                if res is True: success += 1
                p_bar.progress((i + 1) / len(job['targets']))
                status.info(f"📊 Status: {i+1}/{len(job['targets'])} | Success: {success} | Current ID: {job['email']}")

        # Finish Job
        st.session_state.sending_active = False
        st.session_state.job_snapshot = None
        st.success(f"Task Done! {success} Mails Sent Successfully.")
        st.balloons()
        time.sleep(2)
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)
