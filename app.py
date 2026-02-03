import streamlit as st
import smtplib
import time
import concurrent.futures
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr, make_msgid

# --- Page Config ---
st.set_page_config(page_title="Radhe Radhe Turbo Mailer", layout="wide")

# --- CSS (Exactly like your original) ---
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

# --- Authentication ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
    if st.button("LOGIN"):
        if u == "@#2026@#" and p == "@#2026@#":
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("Invalid Credentials")
else:
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center;'>📧 Fast Mail Launcher Pro</h2>", unsafe_allow_html=True)
    
    # --- UI with 6 Columns (Exactly as requested) ---
    col1, col2 = st.columns(2)
    with col1: s_name = st.text_input("Sender Name", key="sn")
    with col2: s_email = st.text_input("Your Gmail", key="se")
    
    col3, col4 = st.columns(2)
    with col3: s_pass = st.text_input("App Password", type="password", key="sp")
    with col4: subject = st.text_input("Subject", key="sub")
    
    col5, col6 = st.columns(2)
    with col5: body = st.text_area("Message Body", height=150, key="msg")
    with col6: recipients_raw = st.text_area("Recipients", height=150, key="rec")

    # --- Worker Function (Anti-Spam Logic) ---
    def send_mail_task(target_email):
        try:
            msg = MIMEMultipart()
            msg['Subject'] = subject
            msg['From'] = formataddr((s_name, s_email))
            msg['To'] = target_email
            msg['Message-ID'] = make_msgid() # Avoids spam filters
            msg['X-Priority'] = '3'
            msg.attach(MIMEText(body, 'html')) # HTML for better delivery

            with smtplib.SMTP('smtp.gmail.com', 587, timeout=15) as server:
                server.starttls()
                server.login(s_email, s_pass)
                server.send_message(msg)
            return True, target_email
        except Exception as e:
            return False, f"{target_email}: {str(e)}"

    # --- Sending Process ---
    if st.button("Send All (Turbo Mode)"):
        email_list = list(dict.fromkeys([e.strip() for e in recipients_raw.replace(',', '\n').split('\n') if e.strip()]))
        
        if s_email and s_pass and email_list:
            progress_bar = st.progress(0)
            status_area = st.empty()
            success_count = 0
            
            # Using ThreadPoolExecutor for real speed
            # Max_workers=5 is safe for Gmail to prevent IP block
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = {executor.submit(send_mail_task, email): email for email in email_list}
                
                for i, future in enumerate(concurrent.futures.as_completed(futures)):
                    success, result = future.result()
                    if success:
                        success_count += 1
                    else:
                        st.error(f"Failed: {result}")
                    
                    # Update Progress
                    progress = (i + 1) / len(email_list)
                    progress_bar.progress(progress)
                    status_area.text(f"🚀 Speed: Active | Sent: {i+1}/{len(email_list)}")

            st.success(f"✅ Mission Accomplished! {success_count} emails delivered.")
            st.balloons()
        else:
            st.warning("Please fill all details and recipient list.")

    if st.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
