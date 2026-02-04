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
st.set_page_config(page_title="Safe Turbo Mailer", layout="wide")

# --- UI Styling ---
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    .main-card {
        background-color: white; padding: 35px; border-radius: 15px;
        box-shadow: 0px 4px 20px rgba(0,0,0,0.1);
        max-width: 1000px; margin: auto; border: 1px solid #ddd;
    }
    header, footer {visibility: hidden;}
    [data-testid="stHeader"] {display: none;}
    div.stButton > button {
        width: 100%; height: 60px; background-color: #1a73e8 !important;
        font-weight: bold; border-radius: 10px; color: white !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- Pro Inbox Bypass Logic ---
def get_safe_content(text):
    # Spam words ko professional synonyms se badalna
    synonyms = {
        r"free": "complimentary", r"win": "attain", r"money": "funds",
        r"urgent": "priority", r"click": "access", r"offer": "opportunity"
    }
    for p, r in synonyms.items():
        text = re.sub(p, r, text, flags=re.IGNORECASE)
    
    # Invisible unique fingerprint for every mail
    fingerprint = f"<div style='display:none;font-size:0px;'>Ref-{uuid.uuid4()}</div>"
    return text.replace('\n', '<br>') + fingerprint

# --- Session Management ---
if 'auth' not in st.session_state: st.session_state.auth = False
if 'sending' not in st.session_state: st.session_state.sending = False
if 'job' not in st.session_state: st.session_state.job = None

# --- Login (Fixed @#2026@#) ---
if not st.session_state.auth:
    _, col, _ = st.columns([1, 1.5, 1])
    with col:
        st.write("### 🔑 Secure Login")
        u = st.text_input("User")
        p = st.text_input("Pass", type="password")
        if st.button("Unlock"):
            if u == "@#2026@#" and p == "@#2026@#":
                st.session_state.auth = True
                st.rerun()
else:
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>📧 Secure Multi-Tasking Mailer</h3>", unsafe_allow_html=True)
    
    # Ye inputs editable rahenge background sending ke waqt bhi
    c1, c2 = st.columns(2)
    with c1: name_input = st.text_input("Sender Name", key="name_box")
    with c2: email_input = st.text_input("Gmail ID", key="email_box")
    
    c3, c4 = st.columns(2)
    with c3: pass_input = st.text_input("App Password", type="password", key="pass_box")
    with c4: sub_input = st.text_input("Subject", key="sub_box")
    
    c5, c6 = st.columns(2)
    with c5: body_input = st.text_area("Message Body", height=150, key="body_box")
    with c6: rec_input = st.text_area("Recipients", height=150, key="rec_box")

    # --- Parallel Worker Function ---
    def safe_parallel_engine(target, job_data):
        try:
            msg = MIMEMultipart()
            msg['Subject'] = job_data['s']
            msg['From'] = formataddr((job_data['n'], job_data['e']))
            msg['To'] = target
            msg['Message-ID'] = make_msgid()
            msg['X-Mailer'] = "Microsoft Outlook 16.0" # Tricking Gmail for Inbox
            
            clean_html = f"<html><body>{get_safe_content(job_data['b'])}</body></html>"
            msg.attach(MIMEText(clean_html, 'html'))

            with smtplib.SMTP('smtp.gmail.com', 587, timeout=12) as server:
                server.starttls()
                server.login(job_data['e'], job_data['p'])
                server.send_message(msg)
            return True, target
        except smtplib.SMTPAuthenticationError:
            return "AUTH_ERROR", "App Password wrong"
        except Exception as e:
            return False, str(e)

    # --- Control Logic ---
    if st.session_state.sending:
        st.info(f"⏳ Sending from: {st.session_state.job['e']}")
        st.button("⚙️ BATCH RUNNING (Safe to edit boxes below)", disabled=True)
    else:
        if st.button("🚀 Send All"):
            targets = [e.strip() for e in rec_input.replace(',', '\n').split('\n') if e.strip()]
            if email_input and pass_input and targets:
                # FREEZE: Purani ID ki details lock kar dena
                st.session_state.job = {
                    'n': name_input, 'e': email_input, 'p': pass_input,
                    's': sub_input, 'b': body_input, 'r': targets
                }
                st.session_state.sending = True
                st.rerun()
            else:
                st.error("Details missing!")

    # --- Parallel Execution ---
    if st.session_state.sending and st.session_state.job:
        current_job = st.session_state.job
        p_bar = st.progress(0)
        status = st.empty()
        success = 0
        
        

        # 3 Parallel Workers for High Speed
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = {executor.submit(safe_parallel_engine, em, current_job): em for em in current_job['r']}
            for i, f in enumerate(concurrent.futures.as_completed(futures)):
                res, detail = f.result()
                
                if res == "AUTH_ERROR":
                    st.error(f"❌ Login Failed: {current_job['e']} ka password galat hai!")
                    st.session_state.sending = False
                    st.stop()
                
                if res is True: success += 1
                p_bar.progress((i + 1) / len(current_job['r']))
                status.info(f"🚀 Batch Status: {i+1}/{len(current_job['r'])} | Inboxed: {success}")

        st.session_state.sending = False
        st.session_state.job = None
        st.success(f"Task Done! {success} Mails delivered.")
        st.balloons()
        time.sleep(2)
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)
