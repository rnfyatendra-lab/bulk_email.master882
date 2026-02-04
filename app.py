import streamlit as st
import smtplib
import time
import random
import concurrent.futures
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr, make_msgid

# --- Page Config ---
st.set_page_config(page_title="Safe Mailer Console", layout="wide")

# --- Custom CSS (Exact UI Match) ---
st.markdown("""
    <style>
    .stApp { background-color: #f0f2f6; }
    .main-card {
        background-color: white; padding: 40px; border-radius: 20px;
        box-shadow: 0px 10px 40px rgba(0,0,0,0.1);
        max-width: 1000px; margin: auto; border: 1px solid #e0e4e9;
    }
    input, textarea { color: #333 !important; font-weight: 500 !important; background-color: #ffffff !important; border-radius: 10px !important; }
    div.stButton > button {
        width: 100%; height: 60px; font-size: 18px !important; font-weight: bold;
        border-radius: 12px; border: none; background-color: #4285F4 !important; color: white !important;
    }
    header, footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- Session State for Auth & Rate Limiting ---
if 'auth' not in st.session_state: st.session_state.auth = False
if 'is_sending' not in st.session_state: st.session_state.is_sending = False
if 'usage_history' not in st.session_state: st.session_state.usage_history = {} # {email: [timestamps]}

# --- Helper: Check Rate Limit (28 mails / 1 hour) ---
def check_limit(email):
    now = time.time()
    if email not in st.session_state.usage_history:
        st.session_state.usage_history[email] = []
    
    # Filter only last 1 hour timestamps
    st.session_state.usage_history[email] = [t for t in st.session_state.usage_history[email] if now - t < 3600]
    
    if len(st.session_state.usage_history[email]) >= 28:
        return False
    return True

# --- Login ---
if not st.session_state.auth:
    col_l, col_m, col_r = st.columns([1, 1.5, 1])
    with col_m:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Access"):
            if u == "@#2026@#" and p == "@#2026@#":
                st.session_state.auth = True
                st.rerun()
else:
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    
    # UI Layout (6 Columns Grid)
    c1, c2 = st.columns(2)
    with c1: s_name = st.text_input("", placeholder="Sender Name")
    with c2: s_email = st.text_input("", placeholder="Your Gmail")
    
    c3, c4 = st.columns(2)
    with c3: s_pass = st.text_input("", placeholder="App Password", type="password")
    with c4: subject = st.text_input("", placeholder="Email Subject")
    
    c5, c6 = st.columns(2)
    with c5: body = st.text_area("", placeholder="Message Body", height=200)
    with c6: rec_raw = st.text_area("", placeholder="Recipients (comma / new line)", height=200)

    # --- Worker Function ---
    def send_task(target):
        try:
            msg = MIMEMultipart()
            msg['Subject'] = subject
            msg['From'] = formataddr((s_name, s_email))
            msg['To'] = target
            msg['Message-ID'] = make_msgid()
            msg.attach(MIMEText(body, 'html'))

            with smtplib.SMTP('smtp.gmail.com', 587, timeout=15) as server:
                server.starttls()
                server.login(s_email, s_pass)
                server.send_message(msg)
            
            # Update history on success
            st.session_state.usage_history[s_email].append(time.time())
            return True, target
        except Exception as e:
            return False, f"{target}: {str(e)}"

    # --- Button Logic ---
    st.write("")
    if st.session_state.is_sending:
        st.button("⌛ Sending... Please Wait", disabled=True)
    else:
        btn_send, btn_log = st.columns(2)
        with btn_send:
            if st.button("Send All"):
                if not check_limit(s_email):
                    st.error("❌ Mail Limit Full (28/hr) ❌")
                    st.toast("Wait for 1 hour to reset.", icon="⚠️")
                else:
                    st.session_state.is_sending = True
                    st.rerun()
        with btn_log:
            if st.button("Logout"):
                st.session_state.auth = False
                st.rerun()

    # --- Execution Engine ---
    if st.session_state.is_sending:
        emails = [e.strip() for e in rec_raw.replace(',', '\n').split('\n') if e.strip()]
        if s_email and s_pass and emails:
            p_bar = st.progress(0)
            status = st.empty()
            success = 0
            
            # Parallel Workers = 3
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                futures = {executor.submit(send_task, em): em for em in emails}
                for i, future in enumerate(concurrent.futures.as_completed(futures)):
                    ok, res = future.result()
                    if ok: success += 1
                    p_bar.progress((i + 1) / len(emails))
                    status.info(f"📊 Status: {i+1}/{len(emails)} sent | Current: {res}")
            
            st.session_state.is_sending = False
            st.success(f"Final: {success} Mails Inboxed!")
            st.balloons()
            time.sleep(2)
            st.rerun()
        else:
            st.session_state.is_sending = False
            st.error("Details missing!")
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)
