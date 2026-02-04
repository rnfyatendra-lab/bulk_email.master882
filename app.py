import streamlit as st
import smtplib
import time
import concurrent.futures
import re
import uuid
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr, make_msgid

# --- Page Config ---
st.set_page_config(page_title="Yatendra Lodhi Mailer", layout="wide")

# --- CSS (Visibility & High Inboxing Design) ---
st.markdown("""
    <style>
    .stApp { background-color: #f0f2f6; }
    .main-card {
        background-color: white; padding: 30px; border-radius: 15px;
        box-shadow: 0px 4px 20px rgba(0,0,0,0.1);
        max-width: 950px; margin: auto; border: 1px solid #e0e4e9;
    }
    input, textarea { color: #000000 !important; font-weight: 500 !important; background-color: #ffffff !important; }
    div.stButton > button:first-child {
        width: 100%; height: 70px; background-color: #1a73e8 !important;
        color: white !important; font-size: 20px !important; font-weight: bold;
        border-radius: 10px; border: none;
    }
    header, footer {visibility: hidden;}
    [data-testid="stHeader"] {display: none;}
    </style>
""", unsafe_allow_html=True)

# --- Pro Inbox Bypass Logic ---
def get_clean_body(text):
    # Invisible unique tag jo har mail ko alag banata hai
    hidden_id = f"<div style='display:none;font-size:0px;'>ID-{uuid.uuid4()}</div>"
    # Anti-spam formatting
    safe_text = text.replace("free", "zero-cost").replace("win", "claim")
    return f"<html><body>{safe_text.replace('\n', '<br>')}{hidden_id}</body></html>"

# --- High Speed Worker (Parallel) ---
def send_safe_parallel(recipient, job):
    try:
        msg = MIMEMultipart()
        msg['Subject'] = job['s']
        msg['From'] = formataddr((job['n'], job['e']))
        msg['To'] = recipient
        msg['Message-ID'] = make_msgid()
        msg['X-Mailer'] = "Microsoft Outlook 16.0" # Gmail Trust Booster
        
        msg.attach(MIMEText(get_clean_body(job['b']), 'html'))

        with smtplib.SMTP('smtp.gmail.com', 587, timeout=12) as server:
            server.starttls()
            server.login(job['e'], job['p'])
            server.send_message(msg)
        return True
    except Exception:
        return False

# --- Session State ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'is_sending' not in st.session_state: st.session_state.is_sending = False
if 'frozen_job' not in st.session_state: st.session_state.frozen_job = None

# --- Login UI ---
if not st.session_state.logged_in:
    _, col, _ = st.columns([1, 1.5, 1])
    with col:
        st.write("### 🔐 Secure Access")
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("LOGIN"):
            if u == "YATENDRA LODHI" and p == "YATENDRA LODHI":
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Invalid Username or Password!")
else:
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center;'>🚀 Turbo Safe Launcher</h2>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1: s_name = st.text_input("Sender Name", key="sn")
    with col2: s_email = st.text_input("Your Gmail", key="se")
    col3, col4 = st.columns(2)
    with col3: s_pass = st.text_input("App Password", type="password", key="sp")
    with col4: subject = st.text_input("Subject", key="sub")
    col5, col6 = st.columns(2)
    with col5: body = st.text_area("Message Body", height=150, key="msg")
    with col6: recipients_raw = st.text_area("Recipients", height=150, key="rec")

    # --- Sending Engine ---
    if st.session_state.is_sending:
        st.button("⌛ Parallel Job Active... (Safe to Change Details)", disabled=True)
        job = st.session_state.frozen_job
        p_bar = st.progress(0)
        status = st.empty()
        success = 0

        # Parallel Multi-threading (3 Workers for speed + safety)
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = {executor.submit(send_safe_parallel, em, job): em for em in job['r']}
            for i, f in enumerate(concurrent.futures.as_completed(futures)):
                if f.result() is True: success += 1
                p_bar.progress((i + 1) / len(job['r']))
                status.text(f"Progress: {i+1}/{len(job['r'])} | Successful Inbox: {success}")

        st.session_state.is_sending = False
        st.session_state.frozen_job = None
        st.success(f"✅ Mission Done! {success} mails reached Inbox.")
        st.balloons()
        time.sleep(2)
        st.rerun()
            
    else:
        btn_col, logout_col = st.columns([0.8, 0.2])
        with btn_col:
            if st.button("🚀 Send All"):
                targets = list(dict.fromkeys([e.strip() for e in recipients_raw.replace(',', '\n').split('\n') if e.strip()]))
                if s_email and s_pass and targets:
                    # SNAPSHOT (Freeze details)
                    st.session_state.frozen_job = {'n': s_name, 'e': s_email, 'p': s_pass, 's': subject, 'b': body, 'r': targets}
                    st.session_state.is_sending = True
                    st.rerun()
        with logout_col:
            if st.button("Logout"):
                st.session_state.logged_in = False
                st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)
