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
st.set_page_config(page_title="Console", layout="wide")

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
    input, textarea { border-radius: 8px !important; }
    div.stButton > button {
        width: 100%; height: 60px; background-color: #1a73e8 !important;
        font-weight: bold; border-radius: 10px; color: white !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- Inbox-Safe Sanitizer ---
def sanitize_content(text):
    synonyms = {
        r"free": "complimentary", r"win": "attain", r"money": "funds",
        r"urgent": "priority", r"click": "visit", r"offer": "proposal"
    }
    for p, r in synonyms.items():
        text = re.sub(p, r, text, flags=re.IGNORECASE)
    
    # Hidden unique string for every mail to bypass filters
    fingerprint = f"<div style='display:none;font-size:0;'>{uuid.uuid4()}</div>"
    return text.replace('\n', '<br>') + fingerprint

# --- Session State Management ---
if 'auth' not in st.session_state: st.session_state.auth = False
if 'sending' not in st.session_state: st.session_state.sending = False
if 'current_job' not in st.session_state: st.session_state.current_job = None
if 'limit_map' not in st.session_state: st.session_state.limit_map = {}

# --- Authentication ---
if not st.session_state.auth:
    _, col, _ = st.columns([1, 1.5, 1])
    with col:
        st.write("### 🔑 Console Login")
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Access"):
            if u == "@#2026@#" and p == "@#2026@#":
                st.session_state.auth = True
                st.rerun()
else:
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>📧 Secure Turbo Mailer</h3>", unsafe_allow_html=True)
    
    # Input Fields (Ye hamesha edit ho sakte hain bina sending ko roke)
    c1, c2 = st.columns(2)
    with c1: input_name = st.text_input("Sender Name", key="name_box")
    with c2: input_email = st.text_input("Your Gmail ID", key="email_box")
    
    c3, c4 = st.columns(2)
    with c3: input_pass = st.text_input("App Password", type="password", key="pass_box")
    with c4: input_sub = st.text_input("Subject", key="sub_box")
    
    c5, c6 = st.columns(2)
    with c5: input_body = st.text_area("Message Body", height=180, key="body_box")
    with c6: input_rec = st.text_area("Recipients", height=180, key="rec_box")

    # --- Internal Mailing Worker ---
    def mailing_engine(target_email, job_data):
        try:
            msg = MIMEMultipart()
            msg['Subject'] = job_data['subject']
            msg['From'] = formataddr((job_data['name'], job_data['email']))
            msg['To'] = target_email
            msg['Message-ID'] = make_msgid()
            msg['X-Mailer'] = "Microsoft Outlook 16.0"
            
            clean_html = f"<html><body>{sanitize_content(job_data['body'])}</body></html>"
            msg.attach(MIMEText(clean_html, 'html'))

            with smtplib.SMTP('smtp.gmail.com', 587, timeout=10) as server:
                server.starttls()
                server.login(job_data['email'], job_data['pass'])
                server.send_message(msg)
            
            st.session_state.limit_map[job_data['email']].append(time.time())
            return True, target_email
        except smtplib.SMTPAuthenticationError:
            return "AUTH_ERROR", "App Password wrong"
        except Exception as e:
            return False, str(e)

    # --- Control Row ---
    st.write("")
    if st.session_state.sending:
        st.warning("⚠️ A sending job is already active in background. Please wait.")
        st.button("⌛ JOB ACTIVE...", disabled=True)
    else:
        if st.button("🚀 Send All"):
            target_list = [e.strip() for e in input_rec.replace(',', '\n').split('\n') if e.strip()]
            
            # Check 28/hr limit for CURRENTly entered ID
            now = time.time()
            if input_email not in st.session_state.limit_map: st.session_state.limit_map[input_email] = []
            st.session_state.limit_map[input_email] = [t for t in st.session_state.limit_map[input_email] if now - t < 3600]

            if len(st.session_state.limit_map[input_email]) >= 28:
                st.error(f"❌ Limit Full (28/hr) for {input_email}")
            elif not input_email or not input_pass or not target_list:
                st.warning("All fields are required!")
            else:
                # FREEZE JOB DATA: Purani ID ki details ko lock kar dena
                st.session_state.current_job = {
                    'name': input_name,
                    'email': input_email,
                    'pass': input_pass,
                    'subject': input_sub,
                    'body': input_body,
                    'targets': target_list
                }
                st.session_state.sending = True
                st.rerun()

    # --- Background Execution Engine ---
    if st.session_state.sending and st.session_state.current_job:
        job = st.session_state.current_job
        p_bar = st.progress(0)
        status = st.empty()
        success = 0
        
        # 

        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            # Job data pass kar rahe hain taaki agar UI change bhi ho jaye, process wahi rahe
            futures = {executor.submit(mailing_engine, em, job): em for em in job['targets']}
            for i, f in enumerate(concurrent.futures.as_completed(futures)):
                res, detail = f.result()
                
                if res == "AUTH_ERROR":
                    st.error(f"❌ Authentication Failed for {job['email']} (Check App Password)")
                    st.session_state.sending = False
                    st.stop()
                
                if res is True: success += 1
                p_bar.progress((i + 1) / len(job['targets']))
                status.info(f"📊 Sending from: {job['email']} | Progress: {i+1}/{len(job['targets'])} | Sent: {success}")

        st.session_state.sending = False
        st.session_state.current_job = None
        st.success(f"Job Complete! {success} mails delivered successfully.")
        st.balloons()
        time.sleep(2)
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)
