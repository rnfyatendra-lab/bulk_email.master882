import streamlit as st
import smtplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formatdate, make_msgid
from concurrent.futures import ThreadPoolExecutor

# --- Page Config ---
st.set_page_config(page_title="Radhe Radhe Mailer", layout="wide")

# --- CSS (Exact Same Design) ---
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

# --- Thread-Safe Engine ---
def send_safe_email(r_id, job):
    try:
        # SMTP setup
        server = smtplib.SMTP('smtp.gmail.com', 587, timeout=12)
        server.starttls()
        server.login(job['e'], job['p'])
        
        # Inbox-Friendly Message Construction
        msg = MIMEMultipart()
        msg['From'] = f"{job['n']} <{job['e']}>"
        msg['To'] = r_id
        msg['Subject'] = job['s']
        msg['Date'] = formatdate(localtime=True)
        msg['Message-ID'] = make_msgid() # Unique ID for each mail to avoid spam filters
        
        msg.attach(MIMEText(job['b'], 'plain'))
        
        server.send_message(msg)
        server.quit()
        return True
    except:
        return False

# --- Session Management ---
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
    st.markdown("<h2 style='text-align: center;'>📧 Fast Mail Launcher</h2>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1: s_name = st.text_input("Sender Name", key="sn")
    with col2: s_email = st.text_input("Your Gmail", key="se")
    col3, col4 = st.columns(2)
    with col3: s_pass = st.text_input("App Password", type="password", key="sp")
    with col4: subject = st.text_input("Subject", key="sub")
    col5, col6 = st.columns(2)
    with col5: body = st.text_area("Message Body", height=150, key="msg")
    with col6: recipients_raw = st.text_area("Recipients", height=150, key="rec")

    # --- Engine ---
    if st.session_state.is_sending:
        job = st.session_state.frozen_job
        recipients = job['r']
        
        start_time = time.time()
        # Parallel Batches: 3 workers at a time (as per your 9 batch logic) 
        # but configured for 2-3 sec total time.
        with ThreadPoolExecutor(max_workers=10) as executor:
            results = list(executor.map(lambda r: send_safe_email(r, job), recipients))
        
        duration = round(time.time() - start_time, 2)
        st.success(f"✅ Fast Delivery Done! Sent: {sum(results)}/ {len(recipients)} in {duration}s")
        st.session_state.is_sending = False
        st.balloons()
        time.sleep(2)
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
