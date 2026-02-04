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

# --- Professional UI Styling ---
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
def bypass_cleaner(text):
    # Spam triggers ko bypass karne ke liye synonyms
    mapping = {
        r"free": "zero-cost", r"win": "attain", r"money": "funds",
        r"urgent": "important", r"offer": "opportunity", r"click": "proceed"
    }
    for p, r in mapping.items():
        text = re.sub(p, r, text, flags=re.IGNORECASE)
    
    # Hidden fingerprint for Gmail Inbox
    tag = f"<div style='display:none; color:white; font-size:0px;'>ID-{uuid.uuid4()}</div>"
    return text.replace('\n', '<br>') + tag

# --- Session State ---
if 'auth' not in st.session_state: st.session_state.auth = False
if 'is_sending' not in st.session_state: st.session_state.is_sending = False
if 'job' not in st.session_state: st.session_state.job = None

# --- Login (Fixed Credentials) ---
if not st.session_state.auth:
    col_l, col_m, col_r = st.columns([1, 1.5, 1])
    with col_m:
        st.write("### 🔐 Console Access")
        u = st.text_input("User")
        p = st.text_input("Pass", type="password")
        if st.button("UNLOCK"):
            if u == "@#2026@#" and p == "@#2026@#":
                st.session_state.auth = True
                st.rerun()
            else:
                st.error("Invalid Login Details!")
else:
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center;'>📧 Secure Turbo Mailer</h2>", unsafe_allow_html=True)
    
    # Input Layout
    c1, c2 = st.columns(2)
    with c1: s_name = st.text_input("Sender Name (Display)", key="sn")
    with c2: s_email = st.text_input("Your Gmail", key="se")
    
    c3, c4 = st.columns(2)
    with c3: s_pass = st.text_input("App Password", type="password", key="sp")
    with c4: subject = st.text_input("Subject", key="sub")
    
    c5, c6 = st.columns(2)
    with c5: body = st.text_area("Message Body", height=150, key="msg")
    with c6: rec_raw = st.text_area("Recipients", height=150, key="rec")

    # --- High-Speed Worker ---
    def mailing_worker(target, frozen_data):
        try:
            msg = MIMEMultipart()
            msg['Subject'] = frozen_data['s']
            msg['From'] = formataddr((frozen_data['n'], frozen_data['e']))
            msg['To'] = target
            msg['Message-ID'] = make_msgid()
            msg['X-Mailer'] = "Microsoft Outlook 16.0" # Inbox Booster

            html_body = f"<html><body>{bypass_cleaner(frozen_data['b'])}</body></html>"
            msg.attach(MIMEText(html_body, 'html'))

            with smtplib.SMTP('smtp.gmail.com', 587, timeout=12) as server:
                server.starttls()
                server.login(frozen_data['e'], frozen_data['p'])
                server.send_message(msg)
            return True, target
        except smtplib.SMTPAuthenticationError:
            return "AUTH_ERROR", "App Password wrong"
        except Exception as e:
            return False, str(e)

    # --- Controller ---
    if st.session_state.is_sending:
        st.button("⌛ Sending Active... (Details Locked)", disabled=True)
        job = st.session_state.job
        p_bar = st.progress(0)
        status = st.empty()
        success = 0
        
        

        # Parallel Execution (3 Workers for High Speed)
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = {executor.submit(mailing_worker, em, job): em for em in job['r']}
            for i, f in enumerate(concurrent.futures.as_completed(futures)):
                res, detail = f.result()
                
                if res == "AUTH_ERROR":
                    st.error(f"❌ LOGIN FAILED: {job['e']} ka password check karein.")
                    st.session_state.is_sending = False
                    st.stop()
                
                if res is True: success += 1
                p_bar.progress((i + 1) / len(job['r']))
                status.info(f"🚀 Batch Progress: {i+1}/{len(job['r'])} | Inboxed: {success}")

        st.session_state.is_sending = False
        st.session_state.job = None
        st.success(f"Final: {success} Mails Sent Successfully!")
        st.balloons()
        time.sleep(2)
        st.rerun()
            
    else:
        btn_col, logout_col = st.columns([0.8, 0.2])
        with btn_col:
            if st.button("Send All"):
                targets = [e.strip() for e in rec_raw.replace(',', '\n').split('\n') if e.strip()]
                if s_email and s_pass and targets:
                    # SNAPSHOT (Freeze details)
                    st.session_state.job = {
                        'n': s_name, 'e': s_email, 'p': s_pass,
                        's': subject, 'b': body, 'r': targets
                    }
                    st.session_state.is_sending = True
                    st.rerun()
                else:
                    st.warning("Please fill all details correctly!")

        with logout_col:
            if st.button("Logout"):
                st.session_state.auth = False
                st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)
