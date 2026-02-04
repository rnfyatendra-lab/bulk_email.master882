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
st.set_page_config(page_title="Console", layout="wide")

# --- UI Styling (Image 1 Exact Style) ---
st.markdown("""
    <style>
    .stApp { background-color: #f0f2f6; }
    .main-card {
        background-color: white; padding: 40px; border-radius: 20px;
        box-shadow: 0px 10px 40px rgba(0,0,0,0.1);
        max-width: 1000px; margin: auto; margin-top: 50px; border: 1px solid #e0e4e9;
    }
    input, textarea { 
        color: #000 !important; font-weight: 500 !important; 
        background-color: #fff !important; border: 1px solid #dcdcdc !important;
        border-radius: 10px !important; padding: 15px !important;
    }
    div.stButton > button {
        width: 100%; height: 65px; background-color: #4A90E2 !important;
        color: white !important; font-size: 18px !important; font-weight: bold;
        border-radius: 12px; border: none;
    }
    header, footer {visibility: hidden;}
    [data-testid="stHeader"] {display: none;}
    </style>
""", unsafe_allow_html=True)

# --- Anti-Spam Synonym Logic ---
def get_safe_content(text):
    spam_words = {
        r"free": "complimentary", r"win": "attain", r"money": "funds",
        r"urgent": "important", r"click": "visit", r"offer": "opportunity"
    }
    for p, r in spam_words.items():
        text = re.sub(p, r, text, flags=re.IGNORECASE)
    return text

# --- Session Management ---
if 'auth' not in st.session_state: st.session_state.auth = False
if 'sending' not in st.session_state: st.session_state.sending = False
if 'job_data' not in st.session_state: st.session_state.job_data = None
if 'limit_logs' not in st.session_state: st.session_state.limit_logs = {}

# --- Login ---
if not st.session_state.auth:
    col_l, col_m, col_r = st.columns([1, 1.5, 1])
    with col_m:
        st.write("### Login")
        u = st.text_input("User")
        p = st.text_input("Pass", type="password")
        if st.button("Unlock"):
            if u == "@#2026@#" and p == "@#2026@#":
                st.session_state.auth = True
                st.rerun()
else:
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>🛡️ Secure Mail Console</h3>", unsafe_allow_html=True)
    
    # 6-Column Input Grid
    c1, c2 = st.columns(2)
    with c1: input_name = st.text_input("Sender Name (Optional)", key="name_in")
    with c2: input_email = st.text_input("Your Gmail", key="email_in")
    
    c3, c4 = st.columns(2)
    with c3: input_pass = st.text_input("App Password", type="password", key="pass_in")
    with c4: input_sub = st.text_input("Email Subject", key="sub_in")
    
    c5, c6 = st.columns(2)
    with c5: input_body = st.text_area("Message Body", height=200, key="body_in")
    with c6: input_rec = st.text_area("Recipients (one per line)", height=200, key="rec_in")

    # --- Worker Function (Using Frozen Data) ---
    def turbo_worker(target_email):
        job = st.session_state.job_data
        try:
            processed_body = get_safe_content(job['body']).replace('\n', '<br>')
            msg = MIMEMultipart()
            msg['Subject'] = job['subject']
            # Agar name fill kiya hai toh wo dikhega, warna blank
            msg['From'] = formataddr((job['sender_name'], job['sender_email']))
            msg['To'] = target_email
            msg['Message-ID'] = make_msgid()
            
            # Unique hidden tag to avoid duplication filters
            h_tag = f"<div style='display:none;'>Ref-{uuid.uuid4()}</div>"
            msg.attach(MIMEText(f"<html><body>{processed_body}{h_tag}</body></html>", 'html'))

            with smtplib.SMTP('smtp.gmail.com', 587, timeout=10) as server:
                server.starttls()
                server.login(job['sender_email'], job['app_pass'])
                server.send_message(msg)
            
            st.session_state.limit_logs[job['sender_email']].append(time.time())
            return True, target_email
        except Exception as e:
            return False, str(e)

    # --- Control Section ---
    st.write("")
    if st.session_state.sending:
        st.button("⌛ Sending Active (Details below are locked for current job)", disabled=True)
    else:
        b1, b2 = st.columns(2)
        with b1:
            if st.button("Send All"):
                # Job data freeze kar rahe hain taaki input change karne se purana process na ruke
                email_list = [l.strip() for l in input_rec.replace(',', '\n').split('\n') if l.strip()]
                
                now = time.time()
                if input_email not in st.session_state.limit_logs: st.session_state.limit_logs[input_email] = []
                st.session_state.limit_logs[input_email] = [t for t in st.session_state.limit_logs[input_email] if now-t < 3600]
                
                if len(st.session_state.limit_logs[input_email]) >= 28:
                    st.error(f"❌ Limit Reached for {input_email} (28/hr). Change ID. ❌")
                elif not email_list:
                    st.warning("Please add recipients!")
                else:
                    st.session_state.job_data = {
                        'sender_name': input_name,
                        'sender_email': input_email,
                        'app_pass': input_pass,
                        'subject': input_sub,
                        'body': input_body,
                        'recipients': email_list
                    }
                    st.session_state.sending = True
                    st.rerun()
        with b2:
            if st.button("Logout"):
                st.session_state.auth = False
                st.rerun()

    # --- Parallel Execution Engine ---
    if st.session_state.sending and st.session_state.job_data:
        targets = st.session_state.job_data['recipients']
        current_id = st.session_state.job_data['sender_email']
        
        p_bar = st.progress(0)
        status = st.empty()
        success = 0
        
        # Turbo Speed: 3 parallel workers
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = {executor.submit(turbo_worker, em): em for em in targets}
            for i, f in enumerate(concurrent.futures.as_completed(futures)):
                # Hourly check
                if len(st.session_state.limit_logs[current_id]) >= 28:
                    st.warning("ID limit reached. Process paused.")
                    break
                
                ok, res = f.result()
                if ok: success += 1
                p_bar.progress((i+1)/len(targets))
                status.info(f"🚀 Sent: {i+1}/{len(targets)} | Success: {success} | Current: {res}")

        st.session_state.sending = False
        st.session_state.job_data = None # Task complete, clear frozen job
        st.success(f"Final: {success} Mails Inboxed Successfully!")
        st.balloons()
        time.sleep(2)
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)
