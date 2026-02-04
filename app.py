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
st.set_page_config(page_title="Turbo Safe Mailer", layout="wide")

# --- UI Styling ---
st.markdown("""
    <style>
    .stApp { background-color: #f0f2f6; }
    .main-card {
        background-color: white; padding: 35px; border-radius: 15px;
        box-shadow: 0px 4px 20px rgba(0,0,0,0.1);
        max-width: 950px; margin: auto; border: 1px solid #e0e4e9;
    }
    input, textarea { color: #000 !important; font-weight: 500 !important; background-color: #fff !important; border: 1px solid #ccc !important;}
    div.stButton > button {
        width: 100%; height: 70px; background-color: #4285F4 !important;
        color: white !important; font-size: 20px !important; font-weight: bold;
        border-radius: 12px; border: none;
    }
    header, footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- Advanced Spam Word Sanitizer (Contextual English Synonyms) ---
def advanced_sanitizer(text):
    # Professional English replacements for common spam triggers
    replacements = {
        r"free": "complimentary",
        r"win": "attain",
        r"winner": "achiever",
        r"money": "funds",
        r"cash": "currency",
        r"offer": "proposal",
        r"urgent": "important",
        r"congratulations": "greetings",
        r"click here": "proceed via link",
        r"buy now": "secure today",
        r"gift": "reward",
        r"unlimited": "extensive"
    }
    safe_text = text
    for pattern, replacement in replacements.items():
        safe_text = re.sub(pattern, replacement, safe_text, flags=re.IGNORECASE)
    return safe_text

# --- Session State ---
if 'auth' not in st.session_state: st.session_state.auth = False
if 'sending' not in st.session_state: st.session_state.sending = False
if 'limit_history' not in st.session_state: st.session_state.limit_history = {}

# --- Login Logic ---
if not st.session_state.auth:
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        u = st.text_input("Username", placeholder="Enter Username")
        p = st.text_input("Password", type="password", placeholder="Enter Password")
        if st.button("UNLOCK SYSTEM"):
            if u == "@#2026@#" and p == "@#2026@#":
                st.session_state.auth = True
                st.rerun()
else:
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    
    # 6 Column Grid
    c1, c2 = st.columns(2)
    with c1: s_name = st.text_input("Sender Name", placeholder="Display Name")
    with c2: s_email = st.text_input("Your Gmail", placeholder="Current Active ID")
    
    c3, c4 = st.columns(2)
    with c3: s_pass = st.text_input("App Password", type="password", placeholder="16-digit app password")
    with c4: subject = st.text_input("Subject", placeholder="Email Subject")
    
    c5, c6 = st.columns(2)
    with c5: body = st.text_area("Message Body (Auto-Cleaned)", height=200)
    with c6: rec_raw = st.text_area("Recipients", height=200, placeholder="Emails (one per line)")

    # --- High Speed Worker Function ---
    def send_engine(target):
        try:
            # Preserving lines and swapping spam words with professional English
            processed_body = advanced_sanitizer(body).replace('\n', '<br>')
            
            msg = MIMEMultipart()
            msg['Subject'] = subject
            msg['From'] = formataddr((s_name, s_email))
            msg['To'] = target
            msg['Message-ID'] = make_msgid()
            # Random hidden string for uniqueness
            hidden_id = f"<div style='display:none; color:white;'>Ref:{random.randint(1000,9999)}</div>"
            msg.attach(MIMEText(f"<html><body>{processed_body}{hidden_id}</body></html>", 'html'))

            with smtplib.SMTP('smtp.gmail.com', 587, timeout=10) as server:
                server.starttls()
                server.login(s_email, s_pass)
                server.send_message(msg)
            
            # Save timestamp for current ID's limit
            st.session_state.limit_history[s_email].append(time.time())
            return True, target
        except Exception as e:
            return False, str(e)

    # --- Button Logic ---
    st.write("")
    if st.session_state.sending:
        st.button("🚀 TURBO SENDING IN PROGRESS (System Locked)...", disabled=True)
    else:
        btn_run, btn_out = st.columns([0.8, 0.2])
        with btn_run:
            if st.button("Send All"):
                emails = [e.strip() for e in rec_raw.replace(',', '\n').split('\n') if e.strip()]
                
                # Check 28 mails/hour limit for current ID
                now = time.time()
                if s_email not in st.session_state.limit_history: st.session_state.limit_history[s_email] = []
                st.session_state.limit_history[s_email] = [t for t in st.session_state.limit_history[s_email] if now - t < 3600]
                
                if len(st.session_state.limit_history[s_email]) >= 28:
                    st.error(f"❌ Limit Reached for {s_email} (28/hr). Use different ID. ❌")
                elif not s_email or not emails:
                    st.warning("All fields must be filled!")
                else:
                    st.session_state.sending = True
                    st.rerun()
        with btn_out:
            if st.button("Logout"):
                st.session_state.auth = False
                st.rerun()

    # --- Execution Logic (Parallel 3-Way) ---
    if st.session_state.sending:
        emails = [e.strip() for e in rec_raw.replace(',', '\n').split('\n') if e.strip()]
        p_bar = st.progress(0)
        status_box = st.empty()
        success = 0
        
        # Optimized Parallel execution for Speed
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = {executor.submit(send_engine, em): em for em in emails}
            for i, future in enumerate(concurrent.futures.as_completed(futures)):
                # Stop if ID limit hit during execution
                if len(st.session_state.limit_history[s_email]) >= 28:
                    st.warning("Batch stopped: ID Limit reached.")
                    break
                
                ok, res = future.result()
                if ok: success += 1
                
                # Dynamic Counter
                p_bar.progress((i + 1) / len(emails))
                status_box.info(f"⚡ Batch Active: {i+1}/{len(emails)} | Sent: {success} | Current: {res}")

        st.session_state.sending = False
        st.success(f"Mission Complete: {success} Inboxed.")
        st.balloons()
        time.sleep(2)
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)
