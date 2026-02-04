import streamlit as st
import smtplib
import time
import random
import concurrent.futures
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr, make_msgid

# --- Page Config ---
st.set_page_config(page_title="Safe Mailer 2026", layout="wide")

# --- UI Styling ---
st.markdown("""
    <style>
    .stApp { background-color: #f0f2f6; }
    .main-card {
        background-color: white; padding: 35px; border-radius: 15px;
        box-shadow: 0px 4px 20px rgba(0,0,0,0.1);
        max-width: 950px; margin: auto; border: 1px solid #e0e4e9;
    }
    input, textarea { color: #000 !important; font-weight: 500 !important; background-color: #fff !important; }
    div.stButton > button {
        width: 100%; height: 70px; background-color: #4285F4 !important;
        color: white !important; font-size: 20px !important; font-weight: bold;
        border-radius: 12px; border: none;
    }
    header, footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- Anti-Spam Word Hider ---
def sanitize_content(text):
    # Spam words ko safe words se replace karne ki dictionary
    spam_map = {
        r"free": "complimentary",
        r"win": "achieve",
        r"money": "funds",
        r"cash": "currency",
        r"offer": "opportunity",
        r"click here": "visit link",
        r"buy": "acquire",
        r"urgent": "priority"
    }
    safe_text = text
    for word, replacement in spam_map.items():
        safe_text = re.sub(word, replacement, safe_text, flags=re.IGNORECASE)
    return safe_text

# --- Session State ---
if 'auth' not in st.session_state: st.session_state.auth = False
if 'sending' not in st.session_state: st.session_state.sending = False
if 'limit' not in st.session_state: st.session_state.limit = {}

# --- Login Logic ---
if not st.session_state.auth:
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("LOGIN"):
            if u == "@#2026@#" and p == "@#2026@#":
                st.session_state.auth = True
                st.rerun()
else:
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    
    # 6 Column Grid
    c1, c2 = st.columns(2)
    with c1: s_name = st.text_input("Sender Name")
    with c2: s_email = st.text_input("Your Gmail")
    
    c3, c4 = st.columns(2)
    with c3: s_pass = st.text_input("App Password", type="password")
    with c4: subject = st.text_input("Subject")
    
    c5, c6 = st.columns(2)
    with c5: body = st.text_area("Template (Lines will be preserved)", height=200)
    with c6: rec_raw = st.text_area("Recipients", height=200)

    # --- Secure Sending Engine ---
    def safe_send(target):
        try:
            # Body sanitize and line preservation
            clean_body = sanitize_content(body).replace('\n', '<br>')
            
            msg = MIMEMultipart()
            msg['Subject'] = subject
            msg['From'] = formataddr((s_name, s_email))
            msg['To'] = target
            msg['Message-ID'] = make_msgid()
            msg.attach(MIMEText(f"<html><body>{clean_body}</body></html>", 'html'))

            with smtplib.SMTP('smtp.gmail.com', 587, timeout=15) as server:
                server.starttls()
                server.login(s_email, s_pass)
                server.send_message(msg)
            
            # Record time for rate limit
            st.session_state.limit[s_email].append(time.time())
            return True, target
        except Exception as e:
            return False, str(e)

    # --- Button Logic ---
    st.write("")
    if st.session_state.sending:
        st.button("⌛ SENDING IN PROGRESS...", disabled=True)
    else:
        if st.button("Send All"):
            emails = [e.strip() for e in rec_raw.replace(',', '\n').split('\n') if e.strip()]
            
            # Check Hourly Limit (28/hr)
            now = time.time()
            if s_email not in st.session_state.limit: st.session_state.limit[s_email] = []
            st.session_state.limit[s_email] = [t for t in st.session_state.limit[s_email] if now - t < 3600]
            
            if len(st.session_state.limit[s_email]) >= 28:
                st.error("❌ Mail Limit Full (28/hr) ❌")
            elif not s_email or not emails:
                st.warning("Please fill all details!")
            else:
                st.session_state.sending = True
                st.rerun()

    # --- Execution ---
    if st.session_state.sending:
        emails = [e.strip() for e in rec_raw.replace(',', '\n').split('\n') if e.strip()]
        p_bar = st.progress(0)
        status = st.empty()
        count = 0
        
        # Parallel Processing (3 Workers)
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = {executor.submit(safe_send, em): em for em in emails}
            for i, future in enumerate(concurrent.futures.as_completed(futures)):
                res, info = future.result()
                if res: count += 1
                p_bar.progress((i + 1) / len(emails))
                status.text(f"🚀 Sent: {i+1}/{len(emails)} | Last: {info}")

        st.session_state.sending = False
        st.success(f"Successfully Delivered: {count}")
        st.balloons()
        time.sleep(2)
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)
