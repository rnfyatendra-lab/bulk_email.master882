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

# --- UI Styling (Clean & Pro) ---
st.markdown("""
    <style>
    .stApp { background-color: #f0f2f6; }
    .main-card {
        background-color: white; padding: 40px; border-radius: 20px;
        box-shadow: 0px 10px 40px rgba(0,0,0,0.1);
        max-width: 1000px; margin: auto; margin-top: 20px; border: 1px solid #e0e4e9;
    }
    input, textarea { 
        color: #000 !important; font-weight: 500 !important; 
        background-color: #fff !important; border: 1px solid #dcdcdc !important;
        border-radius: 10px !important;
    }
    div.stButton > button {
        width: 100%; height: 60px; background-color: #4A90E2 !important;
        color: white !important; font-size: 18px !important; font-weight: bold;
        border-radius: 12px; border: none;
    }
    header, footer {visibility: hidden;}
    [data-testid="stHeader"] {display: none;}
    </style>
""", unsafe_allow_html=True)

# --- Email Validator Logic ---
def is_valid_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

# --- Session State ---
if 'auth' not in st.session_state: st.session_state.auth = False
if 'sending' not in st.session_state: st.session_state.sending = False
if 'logs' not in st.session_state: st.session_state.logs = {}

# --- Login ---
if not st.session_state.auth:
    c1, c2, c3 = st.columns([1, 1.5, 1])
    with c2:
        st.write("### 🔐 Secure Login")
        u = st.text_input("User")
        p = st.text_input("Pass", type="password")
        if st.button("Unlock"):
            if u == "@#2026@#" and p == "@#2026@#":
                st.session_state.auth = True
                st.rerun()
else:
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    
    # Input Grid
    col1, col2 = st.columns(2)
    with col1: s_name = st.text_input("Sender Name (Optional)", key="sn")
    with col2: s_email = st.text_input("Your Gmail", key="se")
    
    col3, col4 = st.columns(2)
    with col3: s_pass = st.text_input("App Password", type="password", key="sp")
    with col4: subject = st.text_input("Email Subject", key="sub")
    
    col5, col6 = st.columns(2)
    with col5: body = st.text_area("Message Body", height=200, key="msg")
    with col6: rec_raw = st.text_area("Recipients (One per line)", height=200, key="rec")

    # --- Worker Function ---
    def worker(target):
        try:
            msg = MIMEMultipart()
            msg['Subject'] = subject
            msg['From'] = formataddr((s_name, s_email))
            msg['To'] = target
            msg['Message-ID'] = make_msgid()
            
            # Anti-Spam Tag
            h_tag = f"<div style='display:none;'>ID-{uuid.uuid4()}</div>"
            msg.attach(MIMEText(f"<html><body>{body.replace(chr(10), '<br>')}{h_tag}</body></html>", 'html'))

            with smtplib.SMTP('smtp.gmail.com', 587, timeout=12) as server:
                server.starttls()
                server.login(s_email, s_pass)
                server.send_message(msg)
            
            st.session_state.logs[s_email].append(time.time())
            return True, target
        except Exception as e:
            # Wrong password ya connection error yahan catch hoga
            return False, str(e)

    # --- Buttons ---
    st.write("")
    if st.session_state.sending:
        st.button("⌛ Launching Batches... (Locked)", disabled=True)
    else:
        b1, b2 = st.columns(2)
        with b1:
            if st.button("Send All"):
                # 1. Cleaning & Filtering Valid Emails
                all_emails = [e.strip() for e in rec_raw.replace(',', '\n').split('\n') if e.strip()]
                valid_emails = [e for e in all_emails if is_valid_email(e)]
                skipped = len(all_emails) - len(valid_emails)
                
                # 2. Limit Check
                now = time.time()
                if s_email not in st.session_state.logs: st.session_state.logs[s_email] = []
                st.session_state.logs[s_email] = [t for t in st.session_state.logs[s_email] if now - t < 3600]
                
                if len(st.session_state.logs[s_email]) >= 28:
                    st.error(f"❌ Limit Full (28/hr) for {s_email} ❌")
                elif not valid_emails:
                    st.warning(f"No valid emails found! (Skipped: {skipped})")
                else:
                    if skipped > 0: st.toast(f"Skipped {skipped} invalid emails", icon="⚠️")
                    st.session_state.sending = True
                    st.session_state.targets = valid_emails # Store only valid ones
                    st.rerun()
        with b2:
            if st.button("Logout"):
                st.session_state.auth = False
                st.rerun()

    # --- Turbo Parallel Execution ---
    if st.session_state.sending:
        targets = st.session_state.targets
        p_bar = st.progress(0)
        status = st.empty()
        success = 0
        
        

        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
            futures = {ex.submit(worker, em): em for em in targets}
            for i, f in enumerate(concurrent.futures.as_completed(futures)):
                ok, res = f.result()
                if ok:
                    success += 1
                    p_bar.progress((i + 1) / len(targets))
                    status.info(f"⚡ Progress: {i+1}/{len(targets)} | Successfully Inboxed: {success}")
                else:
                    # Authentication Error/Wrong Password Catch
                    st.error(f"🛑 CRITICAL ERROR: {res}")
                    st.session_state.sending = False # RESET BUTTON IMMEDIATELY
                    st.stop()
            
            st.session_state.sending = False
            st.success(f"Task Finished! Total {success} mails delivered.")
            st.balloons()
            time.sleep(2)
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)
