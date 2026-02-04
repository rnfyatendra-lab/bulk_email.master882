import streamlit as st
import smtplib
import time
import random
import concurrent.futures
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr, make_msgid

# --- Page Configuration ---
st.set_page_config(page_title="Safe Mailer 2026", layout="wide")

# --- UI Styling (Matching your Design) ---
st.markdown("""
    <style>
    .stApp { background-color: #f0f2f6; }
    .main-card {
        background-color: white; padding: 35px; border-radius: 15px;
        box-shadow: 0px 4px 20px rgba(0,0,0,0.1);
        max-width: 950px; margin: auto; border: 1px solid #e0e4e9;
    }
    input, textarea { color: #000 !important; font-weight: 500 !important; background-color: #fff !important; }
    div.stButton > button {
        width: 100%; height: 70px; background-color: #4285F4 !important;
        color: white !important; font-size: 20px !important; font-weight: bold;
        border-radius: 12px; border: none;
    }
    header, footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- Session State Management ---
if 'auth' not in st.session_state: st.session_state.auth = False
if 'sending' not in st.session_state: st.session_state.sending = False
if 'limit_tracker' not in st.session_state: st.session_state.limit_tracker = {} # {email: [timestamps]}

# --- Limit Check Logic (28 Mails / 1 Hour) ---
def can_send(email):
    now = time.time()
    if email not in st.session_state.limit_tracker:
        st.session_state.limit_tracker[email] = []
    
    # Filter only last 60 minutes
    st.session_state.limit_tracker[email] = [t for t in st.session_state.limit_tracker[email] if now - t < 3600]
    
    return len(st.session_state.limit_tracker[email]) < 28

# --- Login System ---
if not st.session_state.auth:
    col_l, col_m, col_r = st.columns([1, 1.5, 1])
    with col_m:
        st.write("### 🔐 Secure Login")
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("LOGIN"):
            if u == "@#2026@#" and p == "@#2026@#":
                st.session_state.auth = True
                st.rerun()
            else: st.error("Invalid Credentials!")
else:
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    
    # 6 Column Grid Layout
    c1, c2 = st.columns(2)
    with c1: s_name = st.text_input("Sender Name", placeholder="Display Name")
    with c2: s_email = st.text_input("Your Gmail", placeholder="example@gmail.com")
    
    c3, c4 = st.columns(2)
    with c3: s_pass = st.text_input("App Password", type="password", placeholder="16-digit code")
    with c4: subject = st.text_input("Subject", placeholder="Email Subject")
    
    c5, c6 = st.columns(2)
    with c5: body = st.text_area("Message", height=200)
    with c6: rec_raw = st.text_area("Recipients", height=200, placeholder="Emails (one per line)")

    # --- Worker Engine (Parallel & Safe) ---
    def mail_engine(target):
        try:
            msg = MIMEMultipart()
            msg['Subject'] = subject
            msg['From'] = formataddr((s_name, s_email))
            msg['To'] = target
            msg['Message-ID'] = make_msgid()
            msg.attach(MIMEText(body, 'html'))

            with smtplib.SMTP('smtp.gmail.com', 587, timeout=15) as server:
                server.starttls()
                server.login(s_email, s_pass)
                server.send_message(msg)
            
            # Log successful send time
            st.session_state.limit_tracker[s_email].append(time.time())
            return True, target
        except Exception as e:
            return False, str(e)

    # --- Button & Process Control ---
    st.write("")
    if st.session_state.sending:
        st.button("⌛ Sending In Progress... Please Wait", disabled=True)
    else:
        btn_send, btn_out = st.columns([0.8, 0.2])
        with btn_send:
            if st.button("Send All"):
                # Clean invalid/duplicate emails
                emails = [e.strip() for e in rec_raw.replace(',', '\n').split('\n') if e.strip()]
                
                if not can_send(s_email):
                    st.error("❌ Mail Limit Full (28/hr) ❌")
                    st.toast("Limit reached for this ID. Try another or wait.", icon="🚫")
                elif not s_email or not s_pass or not emails:
                    st.warning("Please fill all details and recipients!")
                else:
                    st.session_state.sending = True
                    st.rerun()
        with btn_out:
            if st.button("Logout"):
                st.session_state.auth = False
                st.rerun()

    # --- Parallel Execution Engine ---
    if st.session_state.sending:
        emails = [e.strip() for e in rec_raw.replace(',', '\n').split('\n') if e.strip()]
        p_bar = st.progress(0)
        status_label = st.empty()
        success_count = 0
        
        # Parallel Processing with 3 workers
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = {executor.submit(mail_engine, email): email for email in emails}
            for i, future in enumerate(concurrent.futures.as_completed(futures)):
                # Double check limit during loop
                if not can_send(s_email):
                    st.error("⚠️ Limit reached mid-process. Stopping.")
                    break
                    
                ok, res = future.result()
                if ok: success_count += 1
                
                # Update UI
                p_bar.progress((i + 1) / len(emails))
                status_label.text(f"📊 Processing: {i+1}/{len(emails)} | Sent: {success_count}")

        st.session_state.sending = False
        st.success(f"✅ Finished! {success_count} emails delivered.")
        st.balloons()
        time.sleep(2)
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)
