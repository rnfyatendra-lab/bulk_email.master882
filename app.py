import streamlit as st
import smtplib
import time
import random
import concurrent.futures
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr, make_msgid

# --- Page Setup ---
st.set_page_config(page_title="Safe Mailer Pro", layout="wide")

# --- Original CSS Styling ---
st.markdown("""
    <style>
    .stApp { background-color: #f0f2f6; }
    .main-card {
        background-color: white; padding: 30px; border-radius: 15px;
        box-shadow: 0px 4px 20px rgba(0,0,0,0.1);
        max-width: 950px; margin: auto; border: 1px solid #e0e4e9;
    }
    input, textarea { color: #000000 !important; font-weight: 500 !important; background-color: #ffffff !important; }
    div.stButton > button:first-child {
        width: 100%; height: 70px; background-color: #4285F4 !important;
        color: white !important; font-size: 20px !important; font-weight: bold;
        border-radius: 10px; border: none;
    }
    header, footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

if 'auth' not in st.session_state: st.session_state.auth = False

# --- Login ---
if not st.session_state.auth:
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
    if st.button("LOGIN"):
        if u == "@#2026@#" and p == "@#2026@#":
            st.session_state.auth = True
            st.rerun()
else:
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center;'>⚡ Turbo Safe Launcher</h2>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1: s_name = st.text_input("Sender Name", key="sn")
    with col2: s_email = st.text_input("Your Gmail", key="se")
    
    col3, col4 = st.columns(2)
    with col3: s_pass = st.text_input("App Password", type="password", key="sp")
    with col4: subject = st.text_input("Subject", key="sub")
    
    col5, col6 = st.columns(2)
    with col5: body = st.text_area("Message Body", height=150, key="msg")
    with col6: recipients_raw = st.text_area("Recipients", height=150, key="rec")

    # --- Optimized Sending Function ---
    def send_mail_safe(target):
        try:
            target = target.strip()
            if not target: return None
            
            msg = MIMEMultipart()
            msg['Subject'] = subject
            msg['From'] = formataddr((s_name, s_email))
            msg['To'] = target
            msg['Message-ID'] = make_msgid() # Essential for Inbox
            msg.attach(MIMEText(body, 'plain'))

            # Port 587 with TLS is more reliable for bulk
            with smtplib.SMTP('smtp.gmail.com', 587, timeout=20) as server:
                server.starttls()
                server.login(s_email, s_pass)
                server.send_message(msg)
            
            # Har mail ke baad 1.2 sec ka gap (Parallel workers ke saath safe hai)
            time.sleep(1.2) 
            return True, target
        except Exception as e:
            return False, f"{target}: {str(e)}"

    if st.button("SEND ALL MAILS"):
        emails = list(dict.fromkeys([e.strip() for e in recipients_raw.replace(',', '\n').split('\n') if e.strip()]))
        
        if s_email and s_pass and emails:
            p_bar = st.progress(0)
            status = st.empty()
            success = 0
            
            # Parallel execution: 3 workers (Best for 25-100 emails)
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                futures = {executor.submit(send_mail_safe, em): em for em in emails}
                
                for i, future in enumerate(concurrent.futures.as_completed(futures)):
                    ok, res = future.result()
                    if ok:
                        success += 1
                    else:
                        st.error(f"Failed: {res}")
                    
                    p_bar.progress((i + 1) / len(emails))
                    status.text(f"Status: {i+1}/{len(emails)} | Sent Successfully: {success}")

            st.success(f"Kaam Khatam! {success} Mails delivered.")
            st.balloons()
        else:
            st.warning("Details check karein!")

    if st.button("Logout"):
        st.session_state.auth = False
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
