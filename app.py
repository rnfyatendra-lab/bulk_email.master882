import streamlit as st
import smtplib
import time
import random
import concurrent.futures
import re
import uuid
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr, make_msgid

# --- Page Config ---
st.set_page_config(page_title="Personalized Turbo Mailer", layout="wide")

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

# --- Smart Word Mapper (Spam to Professional English) ---
def smart_sanitizer(text):
    replacements = {
        r"free": "complimentary",
        r"win": "achieve",
        r"winner": "champion",
        r"money": "funds",
        r"offer": "opportunity",
        r"urgent": "critical",
        r"click here": "use the link",
        r"buy": "secure",
        r"cash": "revenue"
    }
    for pattern, rep in replacements.items():
        text = re.sub(pattern, rep, text, flags=re.IGNORECASE)
    return text

# --- Session State ---
if 'auth' not in st.session_state: st.session_state.auth = False
if 'sending' not in st.session_state: st.session_state.sending = False
if 'tracker' not in st.session_state: st.session_state.tracker = {}

# --- Login Logic ---
if not st.session_state.auth:
    c1, c2, c3 = st.columns([1, 1.5, 1])
    with c2:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("UNLOCK"):
            if u == "@#2026@#" and p == "@#2026@#":
                st.session_state.auth = True
                st.rerun()
else:
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    
    # 6 Column Grid
    c1, c2 = st.columns(2)
    with c1: s_name = st.text_input("Sender Name", placeholder="e.g. Rahul Sharma")
    with c2: s_email = st.text_input("Your Gmail", placeholder="example@gmail.com")
    
    c3, c4 = st.columns(2)
    with c3: s_pass = st.text_input("App Password", type="password")
    with c4: subject_template = st.text_input("Subject", placeholder="Hello {name}, Check this!")
    
    c5, c6 = st.columns(2)
    with c5: body_input = st.text_area("Template (Lines Preserved)", height=220)
    with c6: rec_raw = st.text_area("Recipients (email,name)", height=220, placeholder="raj@gmail.com,Raj\njoy@gmail.com,Joy")

    # --- Turbo Engine ---
    def personalized_engine(data):
        target_email, target_name = data
        try:
            # Customizing Subject & Body
            personal_subject = subject_template.replace("{name}", target_name)
            safe_body = smart_sanitizer(body_input).replace('\n', '<br>')
            
            msg = MIMEMultipart()
            msg['Subject'] = personal_subject
            msg['From'] = formataddr((s_name, s_email))
            msg['To'] = target_email
            msg['Message-ID'] = make_msgid()
            
            # Invisible uniqueness for Gmail AI
            hidden_tag = f"<p style='color:transparent;font-size:0;'>ID:{uuid.uuid4()}</p>"
            msg.attach(MIMEText(f"<html><body>{safe_body}{hidden_tag}</body></html>", 'html'))

            with smtplib.SMTP('smtp.gmail.com', 587, timeout=12) as server:
                server.starttls()
                server.login(s_email, s_pass)
                server.send_message(msg)
            
            st.session_state.tracker[s_email].append(time.time())
            return True, target_email
        except Exception as e:
            return False, str(e)

    # --- Control Row ---
    st.write("")
    if st.session_state.sending:
        st.button("⌛ Launching Parallel Batches... (Button Locked)", disabled=True)
    else:
        btn_send, btn_out = st.columns([0.8, 0.2])
        with btn_send:
            if st.button("Send All"):
                # Parsing: "email,name"
                raw_list = [line.split(',') for line in rec_raw.split('\n') if ',' in line]
                
                now = time.time()
                if s_email not in st.session_state.tracker: st.session_state.tracker[s_email] = []
                st.session_state.tracker[s_email] = [t for t in st.session_state.tracker[s_email] if now - t < 3600]
                
                if len(st.session_state.tracker[s_email]) >= 28:
                    st.error(f"❌ Limit Reached (28/hr) for {s_email} ❌")
                elif not raw_list:
                    st.warning("Please use format: email,name")
                else:
                    st.session_state.sending = True
                    st.rerun()
        with btn_out:
            if st.button("Logout"):
                st.session_state.auth = False
                st.rerun()

    # --- Execution Logic ---
    if st.session_state.sending:
        data_list = [line.split(',') for line in rec_raw.split('\n') if ',' in line]
        p_bar = st.progress(0)
        status_text = st.empty()
        success = 0
        
        # 3 Parallel Workers for Turbo Speed
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = {executor.submit(personalized_engine, d): d for d in data_list}
            for i, future in enumerate(concurrent.futures.as_completed(futures)):
                if len(st.session_state.tracker[s_email]) >= 28: break
                
                ok, res = future.result()
                if ok: success += 1
                p_bar.progress((i + 1) / len(data_list))
                status_text.info(f"🚀 Sent: {i+1}/{len(data_list)} | Successful: {success}")

        st.session_state.sending = False
        st.success(f"Mission Done! {success} Inboxed.")
        st.balloons()
        time.sleep(2)
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)
