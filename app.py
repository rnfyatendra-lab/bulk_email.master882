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
st.set_page_config(page_title="Console", layout="wide")

# --- UI Styling (Clean & Safe) ---
st.markdown("""
    <style>
    .stApp { background-color: #f4f4f9; }
    .main-card {
        background-color: white; padding: 30px; border-radius: 12px;
        box-shadow: 0px 5px 15px rgba(0,0,0,0.05);
        max-width: 950px; margin: auto; border: 1px solid #ddd;
    }
    input, textarea { color: #000000 !important; font-weight: 500 !important; }
    div.stButton > button {
        width: 100%; height: 60px; font-weight: bold; border-radius: 8px;
    }
    .send-btn button { background-color: #1a73e8 !important; color: white !important; font-size: 18px !important; }
    .logout-btn button { background-color: #dc3545 !important; color: white !important; }
    header, footer {visibility: hidden;}
    [data-testid="stHeader"] {display: none;}
    </style>
""", unsafe_allow_html=True)

# --- Inbox Bypass Logic ---
def create_inbox_safe_body(text):
    # Invisible unique tracking ID for every email
    hidden_marker = f"<div style='display:none;font-size:0px;color:white;'>{uuid.uuid4()}</div>"
    return f"<html><body style='font-family: Arial, sans-serif;'>{text.replace('\n', '<br>')}{hidden_marker}</body></html>"

# --- High Speed Parallel Engine ---
def parallel_mail_engine(target, job_data):
    try:
        msg = MIMEMultipart()
        msg['Subject'] = job_data['s']
        msg['From'] = formataddr((job_data['n'], job_data['e']))
        msg['To'] = target
        msg['Message-ID'] = make_msgid()
        # Spoofing as a trusted corporate mailer
        msg['X-Mailer'] = "Microsoft Outlook 16.0" 
        msg['X-Priority'] = '3'

        msg.attach(MIMEText(create_inbox_safe_body(job_data['b']), 'html'))

        with smtplib.SMTP('smtp.gmail.com', 587, timeout=12) as server:
            server.starttls()
            server.login(job_data['e'], job_data['p'])
            server.send_message(msg)
        return True
    except:
        return False

# --- Session Management ---
if 'auth' not in st.session_state: st.session_state.auth = False
if 'is_running' not in st.session_state: st.session_state.is_running = False
if 'frozen_task' not in st.session_state: st.session_state.frozen_task = None

# --- Login UI ---
if not st.session_state.auth:
    _, col, _ = st.columns([1, 1, 1])
    with col:
        st.write("### 🔐 Authentication")
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("LOGIN"):
            if u == "YATENDRA LODHI" and p == "YATENDRA LODHI":
                st.session_state.auth = True
                st.rerun()
            else:
                st.error("Access Denied.")
else:
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    
    # Input fields remain active for next ID preparation
    c1, c2 = st.columns(2)
    with c1: name_ui = st.text_input("Sender Name", key="name")
    with c2: email_ui = st.text_input("Gmail ID", key="email")
    
    c3, c4 = st.columns(2)
    with c3: pass_ui = st.text_input("App Password", type="password", key="pass")
    with c4: sub_ui = st.text_input("Subject", key="subject")
    
    c5, c6 = st.columns(2)
    with c5: body_ui = st.text_area("Message Body", height=150, key="body")
    with c6: list_ui = st.text_area("Recipient List", height=150, key="list")

    # --- Background Sending Process ---
    if st.session_state.is_running:
        st.info(f"⚡ Batch active for: {st.session_state.frozen_task['e']}")
        job = st.session_state.frozen_task
        progress_bar = st.progress(0)
        success_count = 0
        
        

        # Multi-threading (3 Workers) for speed + inbox safety
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = {executor.submit(parallel_mail_engine, email, job): email for email in job['r']}
            for i, f in enumerate(concurrent.futures.as_completed(futures)):
                if f.result() is True: success_count += 1
                progress_bar.progress((i + 1) / len(job['r']))
        
        st.session_state.is_running = False
        st.session_state.frozen_task = None
        st.success(f"Task Completed: {success_count} Inboxed.")
        time.sleep(1)
        st.rerun()
            
    else:
        st.write("")
        col_send, col_logout = st.columns([0.8, 0.2])
        
        with col_send:
            st.markdown('<div class="send-btn">', unsafe_allow_html=True)
            if st.button("Send All"):
                emails = list(dict.fromkeys([x.strip() for x in list_ui.replace(',', '\n').split('\n') if x.strip()]))
                if email_ui and pass_ui and emails:
                    # SNAPSHOT: Data frozen for background process
                    st.session_state.frozen_task = {
                        'n': name_ui, 'e': email_ui, 'p': pass_ui,
                        's': sub_ui, 'b': body_ui, 'r': emails
                    }
                    st.session_state.is_running = True
                    st.rerun()
                else:
                    st.warning("Please fill all details.")
            st.markdown('</div>', unsafe_allow_html=True)

        with col_logout:
            st.markdown('<div class="logout-btn">', unsafe_allow_html=True)
            if st.button("Logout"):
                st.session_state.auth = False
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
