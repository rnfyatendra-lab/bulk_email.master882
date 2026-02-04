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
st.set_page_config(page_title="Radhe Radhe Mailer", layout="wide")

# --- CSS (Visibility & Design) ---
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

# --- Anti-Spam Fixer ---
def hide_spam_content(text):
    words = {r"free": "zero-cost", r"win": "receive", r"money": "funds", r"urgent": "priority"}
    for p, r in words.items():
        text = re.sub(p, r, text, flags=re.IGNORECASE)
    # Invisible unique tracking tag for Inbox delivery
    hidden_tag = f"<div style='display:none;'>Ref-{uuid.uuid4()}</div>"
    return text.replace('\n', '<br>') + hidden_tag

# --- Session State Management ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'is_sending' not in st.session_state: st.session_state.is_sending = False
if 'frozen_job' not in st.session_state: st.session_state.frozen_job = None

# --- Login ---
if not st.session_state.logged_in:
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
    if st.button("LOGIN"):
        if u == "RADHE RADHE" and p == "RADHE RADHE":
            st.session_state.logged_in = True
            st.rerun()
else:
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center;'>📧 Turbo Fast Mail Launcher</h2>", unsafe_allow_html=True)
    
    # UI Inputs
    col1, col2 = st.columns(2)
    with col1: s_name = st.text_input("Sender Name", key="sn")
    with col2: s_email = st.text_input("Your Gmail", key="se")
    col3, col4 = st.columns(2)
    with col3: s_pass = st.text_input("App Password", type="password", key="sp")
    with col4: subject = st.text_input("Subject", key="sub")
    col5, col6 = st.columns(2)
    with col5: body = st.text_area("Message Body", height=150, key="msg")
    with col6: recipients_raw = st.text_area("Recipients", height=150, key="rec")

    # --- Worker Function (High Speed) ---
    def fast_worker(target_email, job):
        try:
            msg = MIMEMultipart()
            msg['Subject'] = job['s']
            msg['From'] = formataddr((job['n'], job['e']))
            msg['To'] = target_email
            msg['Message-ID'] = make_msgid()
            
            content = f"<html><body>{hide_spam_content(job['b'])}</body></html>"
            msg.attach(MIMEText(content, 'html'))

            with smtplib.SMTP('smtp.gmail.com', 587, timeout=12) as server:
                server.starttls()
                server.login(job['e'], job['p'])
                server.send_message(msg)
            return True, target_email
        except smtplib.SMTPAuthenticationError:
            return "AUTH_ERROR", "App Password wrong"
        except Exception as e:
            return False, str(e)

    # --- Execution ---
    if st.session_state.is_sending:
        st.button("⌛ Sending in Progress... (You can edit boxes for next ID)", disabled=True)
        job = st.session_state.frozen_job
        p_bar = st.progress(0)
        status = st.empty()
        success = 0
        
        # Turbo Speed with 3 Parallel Workers
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = {executor.submit(fast_worker, em, job): em for em in job['r']}
            for i, f in enumerate(concurrent.futures.as_completed(futures)):
                res, info = f.result()
                
                if res == "AUTH_ERROR":
                    st.error(f"❌ App Password wrong for {job['e']}!")
                    st.session_state.is_sending = False
                    st.stop()
                
                if res is True: success += 1
                p_bar.progress((i + 1) / len(job['r']))
                status.text(f"🚀 Sent: {i+1}/{len(job['r'])} | Success: {success}")

        st.session_state.is_sending = False
        st.session_state.frozen_job = None
        st.success(f"✅ Mission Complete! {success} mails delivered.")
        st.balloons()
        time.sleep(2)
        st.rerun()
            
    else:
        btn_col, logout_col = st.columns([0.8, 0.2])
        with btn_col:
            if st.button("Send All"):
                unique_emails = list(dict.fromkeys([e.strip() for e in recipients_raw.replace(',', '\n').split('\n') if e.strip()]))
                if s_email and s_pass and unique_emails:
                    # SNAPSHOT/FREEZE current data
                    st.session_state.frozen_job = {
                        'n': s_name, 'e': s_email, 'p': s_pass,
                        's': subject, 'b': body, 'r': unique_emails
                    }
                    st.session_state.is_sending = True
                    st.rerun()
                else:
                    st.warning("Details Check Karein!")

        with logout_col:
            if st.button("Logout"):
                st.session_state.logged_in = False
                st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)
