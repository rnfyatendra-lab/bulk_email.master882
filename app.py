import streamlit as st
import smtplib
import time
import random
import concurrent.futures
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr, make_msgid

# --- Page Config ---
st.set_page_config(page_title="Safe Mailer Pro", layout="centered")

# --- UI Styling ---
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
    .main-box {
        background-color: #1d2129; padding: 30px; border-radius: 15px;
        border: 1px solid #343a40;
    }
    input, textarea { background-color: #2b313e !important; color: white !important; border: 1px solid #454d5e !important; }
    .stButton>button {
        width: 100%; background: linear-gradient(45deg, #FF4B4B, #FF8F8F);
        color: white; font-weight: bold; border-radius: 10px; height: 3em;
    }
    </style>
""", unsafe_allow_html=True)

# --- Authentication ---
if 'auth' not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    st.markdown("<h2 style='text-align:center;'>🔐 System Locked</h2>", unsafe_allow_html=True)
    user_cred = st.text_input("Username")
    pass_cred = st.text_input("Password", type="password")
    if st.button("Access Terminal"):
        if user_cred == "@#2026@#" and pass_cred == "@#2026@#":
            st.session_state.auth = True
            st.rerun()
        else:
            st.error("Access Denied!")
else:
    # --- Dashboard ---
    st.markdown("<h1 style='text-align: center; color: #FF4B4B;'>🚀 Safe Fast Mailer</h1>", unsafe_allow_html=True)
    
    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            s_name = st.text_input("Sender Name", value="Official Notification")
            s_email = st.text_input("Your Gmail")
        with col2:
            s_pass = st.text_input("App Password", type="password")
            subject = st.text_input("Subject Line")
        
        body = st.text_area("Message Body (HTML Supported)", height=150)
        recipients = st.text_area("Recipients (One per line)", height=150)
        
        # Speed Settings
        speed = st.select_slider("Sending Speed Mode", options=["Safe", "Balanced", "Turbo"])
        threads = {"Safe": 2, "Balanced": 5, "Turbo": 10}[speed]

    # --- Sending Logic ---
    def send_mail_secure(to_email):
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = formataddr((s_name, s_email))
            msg['To'] = to_email
            msg['Message-ID'] = make_msgid() # Random ID for anti-spam
            
            # Anti-Spam Headers
            msg['List-Unsubscribe'] = f'<mailto:{s_email}>'
            msg.attach(MIMEText(body, 'html'))

            # Har email ke liye naya handshake (Safe Practice)
            with smtplib.SMTP('smtp.gmail.com', 587, timeout=15) as server:
                server.starttls()
                server.login(s_email, s_pass)
                server.send_message(msg)
            
            # Random delay to mimic human behavior
            time.sleep(random.uniform(0.5, 1.5)) 
            return True, to_email
        except Exception as e:
            return False, f"{to_email}: {str(e)}"

    if st.button("ENGAGE LAUNCHER"):
        email_list = [e.strip() for e in recipients.split('\n') if e.strip()]
        
        if s_email and s_pass and email_list:
            bar = st.progress(0)
            status = st.empty()
            success_count = 0
            
            # Parallel Processing
            with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
                results = list(executor.map(send_mail_secure, email_list))
                
                for i, (ok, res) in enumerate(results):
                    if ok: success_count += 1
                    else: st.warning(f"Failed: {res}")
                    bar.progress((i + 1) / len(email_list))
                    status.info(f"Progress: {i+1}/{len(email_list)} emails processed.")

            st.success(f"Mission Complete! {success_count} emails sent.")
            st.balloons()
        else:
            st.error("Please fill all fields!")

    if st.sidebar.button("Log Out"):
        st.session_state.auth = False
        st.rerun()
