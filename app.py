import streamlit as st
import smtplib
import time
import random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formatdate, make_msgid
from concurrent.futures import ThreadPoolExecutor

# --- Page Config ---
st.set_page_config(page_title="Radhe Radhe Mailer", layout="wide")

# --- CSS (Design Remains Same) ---
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
    </style>
""", unsafe_allow_html=True)

# --- The "Safe-Guard" Sending Function ---
def send_email_safe_logic(r_id, job):
    try:
        # 1. Randomized Delay (Human behavior simulation)
        time.sleep(random.uniform(0.2, 0.6))
        
        server = smtplib.SMTP('smtp.gmail.com', 587, timeout=15)
        server.starttls()
        server.login(job['e'], job['p'])
        
        msg = MIMEMultipart()
        msg['From'] = f"{job['n']} <{job['e']}>"
        msg['To'] = r_id
        msg['Subject'] = job['s']
        
        # 2. Advanced Anti-Spam Headers (Google Compliance)
        msg['Date'] = formatdate(localtime=True)
        msg['Message-ID'] = make_msgid()
        msg['X-Mailer'] = f'SafeMailer-v{random.randint(100,999)}' # Random version ID
        msg['X-Priority'] = '3'
        
        # 3. Plain Text Body (Highest delivery rate)
        msg.attach(MIMEText(job['b'], 'plain'))
        
        server.send_message(msg)
        server.quit()
        return True
    except Exception:
        return False

# --- UI & Auth ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'is_sending' not in st.session_state: st.session_state.is_sending = False

if not st.session_state.logged_in:
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
    if st.button("LOGIN"):
        if u == "RADHE RADHE" and p == "RADHE RADHE":
            st.session_state.logged_in = True
            st.rerun()
else:
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center;'>🛡️ Maximum Safety Mailer</h2>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1: s_name = st.text_input("Sender Name", key="sn")
    with col2: s_email = st.text_input("Your Gmail", key="se")
    col3, col4 = st.columns(2)
    with col3: s_pass = st.text_input("App Password", type="password", key="sp")
    with col4: subject = st.text_input("Subject", key="sub")
    col5, col6 = st.columns(2)
    with col5: body = st.text_area("Message Body", height=150, key="msg")
    with col6: recipients_raw = st.text_area("Recipients", height=150, key="rec")

    # --- Ultra Safe Engine with Counter ---
    if st.session_state.is_sending:
        job = st.session_state.frozen_job
        recips = job['r']
        total = len(recips)
        
        progress_bar = st.progress(0)
        status = st.empty()
        
        success = 0
        # 3 parallel connections (Batches of 3)
        batch_size = 3 
        
        for i in range(0, total, batch_size):
            current_batch = recips[i : i + batch_size]
            
            with ThreadPoolExecutor(max_workers=batch_size) as executor:
                results = list(executor.map(lambda r: send_email_safe_logic(r, job), current_batch))
                success += sum(results)
            
            # Counter & Progress Update
            current_done = min(i + batch_size, total)
            progress_bar.progress(current_done / total)
            status.text(f"Safely Delivered: {current_done}/{total} | Success Rate: {int((success/current_done)*100)}%")
            
            # 4. Mandatory Cool-down between batches (Crucial for Safety)
            if current_done < total:
                time.sleep(1.2) 

        st.success(f"✅ Mission Accomplished! {success} Mails delivered safely.")
        st.session_state.is_sending = False
        st.balloons()
        time.sleep(3)
        st.rerun()

    else:
        btn_col, logout_col = st.columns([0.8, 0.2])
        with btn_col:
            if st.button("Send All"):
                emails = [e.strip() for e in recipients_raw.replace(',', '\n').split('\n') if e.strip()]
                if s_email and s_pass and emails:
                    st.session_state.frozen_job = {'n':s_name, 'e':s_email, 'p':s_pass, 's':subject, 'b':body, 'r':emails}
                    st.session_state.is_sending = True
                    st.rerun()
        with logout_col:
            if st.button("Logout"):
                st.session_state.logged_in = False
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
