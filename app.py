import streamlit as st
import smtplib
import time
import concurrent.futures
import re
import uuid
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr, make_msgid

# --- Page Config & UI Styling ---
st.set_page_config(page_title="Safe Mailer Console", layout="wide")

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

# --- Anti-Spam Logic: Related English Words ---
def hide_spam_words(text):
    mapping = {
        r"free": "complimentary", r"win": "attain", r"money": "funds",
        r"cash": "revenue", r"urgent": "priority", r"offer": "opportunity",
        r"buy": "acquire", r"gift": "reward", r"winner": "achiever"
    }
    for pattern, replacement in mapping.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    return text.replace('\n', '<br>')

# --- Session State Management ---
if 'auth' not in st.session_state: st.session_state.auth = False
if 'sending' not in st.session_state: st.session_state.sending = False
if 'usage_logs' not in st.session_state: st.session_state.usage_logs = {}

# --- Login System ---
if not st.session_state.auth:
    c1, c2, c3 = st.columns([1, 1.5, 1])
    with c2:
        st.write("### 🔐 Login")
        u = st.text_input("User")
        p = st.text_input("Pass", type="password")
        if st.button("Unlock System"):
            if u == "@#2026@#" and p == "@#2026@#":
                st.session_state.auth = True
                st.rerun()
else:
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>📧 Secure Turbo Mailer</h3>", unsafe_allow_html=True)
    
    # 6-Column Input Grid
    col1, col2 = st.columns(2)
    with col1: s_name = st.text_input("Sender Name (Jo aap fill karenge)", key="sn")
    with col2: s_email = st.text_input("Your Gmail", key="se")
    
    col3, col4 = st.columns(2)
    with col3: s_pass = st.text_input("App Password", type="password", key="sp")
    with col4: subject = st.text_input("Email Subject", key="sub")
    
    col5, col6 = st.columns(2)
    with col5: body_input = st.text_area("Message Body", height=200, key="msg")
    with col6: rec_raw = st.text_area("Recipients (one per line)", height=200, key="rec")

    # --- SMTP Worker Engine ---
    def send_mail_worker(target):
        try:
            safe_body = hide_spam_words(body_input)
            msg = MIMEMultipart()
            msg['Subject'] = subject
            msg['From'] = formataddr((s_name, s_email))
            msg['To'] = target
            msg['Message-ID'] = make_msgid()
            
            # Unique ID to bypass filters
            h_id = f"<div style='display:none;'>Ref-{uuid.uuid4()}</div>"
            msg.attach(MIMEText(f"<html><body>{safe_body}{h_id}</body></html>", 'html'))

            with smtplib.SMTP('smtp.gmail.com', 587, timeout=10) as server:
                server.starttls()
                server.login(s_email, s_pass)
                server.send_message(msg)
            
            st.session_state.usage_logs[s_email].append(time.time())
            return True, target
        except smtplib.SMTPAuthenticationError:
            return "AUTH_ERROR", "App Password wrong"
        except Exception as e:
            return False, str(e)

    # --- Button Control ---
    st.write("")
    if st.session_state.sending:
        st.button("⌛ Sending Active... (System Locked)", disabled=True)
    else:
        b1, b2 = st.columns(2)
        with b1:
            if st.button("Send All"):
                emails = [e.strip() for e in rec_raw.replace(',', '\n').split('\n') if e.strip()]
                
                # Hourly Limit Check (28/hr)
                now = time.time()
                if s_email not in st.session_state.usage_logs: st.session_state.usage_logs[s_email] = []
                st.session_state.usage_logs[s_email] = [t for t in st.session_state.usage_logs[s_email] if now - t < 3600]
                
                if len(st.session_state.usage_logs[s_email]) >= 28:
                    st.error(f"❌ Limit Full (28/hr) for {s_email} ❌")
                elif not s_email or not s_pass or not emails:
                    st.warning("Details fill kijiye!")
                else:
                    st.session_state.sending = True
                    st.session_state.target_list = emails
                    st.rerun()
        with b2:
            if st.button("Logout"):
                st.session_state.auth = False
                st.rerun()

    # --- Execution Engine ---
    if st.session_state.sending:
        targets = st.session_state.target_list
        p_bar = st.progress(0)
        counter_text = st.empty()
        success = 0
        
        

        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = {executor.submit(send_mail_worker, em): em for em in targets}
            for i, f in enumerate(concurrent.futures.as_completed(futures)):
                res, info = f.result()
                
                if res == "AUTH_ERROR":
                    st.error("❌ App Password wrong! ❌")
                    st.session_state.sending = False # Reset Button
                    st.stop()
                
                if res is True: success += 1
                
                # Real-time Counter
                p_bar.progress((i + 1) / len(targets))
                counter_text.info(f"📊 Status: {i+1}/{len(targets)} | Inboxed: {success}")

        st.session_state.sending = False
        st.success(f"Task Done! {success} Mails Sent.")
        st.balloons()
        time.sleep(2)
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)
