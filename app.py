import streamlit as st
import smtplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from concurrent.futures import ThreadPoolExecutor

# --- Page Config ---
st.set_page_config(page_title="Radhe Radhe Fast Mailer", layout="wide")

# --- UI Design ---
st.markdown("""
    <style>
    .stApp { background-color: #f0f2f6; }
    .main-card {
        background-color: white; padding: 30px; border-radius: 15px;
        box-shadow: 0px 4px 20px rgba(0,0,0,0.1);
        max-width: 950px; margin: auto; border: 1px solid #e0e4e9;
    }
    input, textarea { color: #000000 !important; font-weight: 500 !important; }
    div.stButton > button:first-child {
        width: 100%; height: 60px; background-color: #FF4B4B !important;
        color: white !important; font-size: 20px !important; font-weight: bold;
        border-radius: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# --- Thread-Safe Fast Function ---
def send_mail_thread(r_id, job):
    try:
        # SMTP setup per thread (Speed ke liye timeout kam rakha hai)
        server = smtplib.SMTP('smtp.gmail.com', 587, timeout=8)
        server.starttls()
        server.login(job['e'], job['p'])
        
        msg = MIMEMultipart()
        msg['From'] = f"{job['n']} <{job['e']}>"
        msg['To'] = r_id
        msg['Subject'] = job['s']
        msg.attach(MIMEText(job['b'], 'plain'))
        
        server.send_message(msg)
        server.quit()
        return True
    except:
        return False

# --- App Logic ---
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
    st.markdown("<h2 style='text-align: center;'>⚡ Super Fast Parallel Mailer</h2>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1: s_name = st.text_input("Sender Name", key="sn")
    with col2: s_email = st.text_input("Your Gmail", key="se")
    col3, col4 = st.columns(2)
    with col3: s_pass = st.text_input("App Password", type="password", key="sp")
    with col4: subject = st.text_input("Subject", key="sub")
    col5, col6 = st.columns(2)
    with col5: body = st.text_area("Message Body", height=150, key="msg")
    with col6: recipients_raw = st.text_area("Recipients", height=150, key="rec")

    if st.session_state.is_sending:
        job = st.session_state.frozen_job
        recipients = job['r']
        
        st.info("🚀 Batch processing shuru ho chuki hai...")
        start_time = time.time()
        
        # max_workers=10 matlab 25 emails lagbhag 2.5 batches mein khatam ho jayenge
        # Isse speed 2-3 seconds ke beech hi rahegi
        with ThreadPoolExecutor(max_workers=10) as executor:
            results = list(executor.map(lambda r: send_mail_thread(r, job), recipients))
        
        end_time = time.time()
        total_time = round(end_time - start_time, 2)
        
        st.success(f"✅ Kaam Ho Gaya! {sum(results)} Mails sent in {total_time} seconds.")
        st.session_state.is_sending = False
        st.balloons()
        if st.button("Naya Batch"): st.rerun()

    else:
        if st.button("🔥 SEND 25 EMAILS IN 2 SECS"):
            emails = [e.strip() for e in recipients_raw.replace(',', '\n').split('\n') if e.strip()]
            if s_email and s_pass and emails:
                st.session_state.frozen_job = {
                    'n': s_name, 'e': s_email, 'p': s_pass,
                    's': subject, 'b': body, 'r': emails
                }
                st.session_state.is_sending = True
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
