import streamlit as st
import smtplib
import time
import random
import concurrent.futures
import re
import uuid
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr, make_msgid

# --- Page Config ---
st.set_page_config(page_title="Console", layout="wide")

# --- UI Styling (Image 1 Style) ---
st.markdown("""
    <style>
    .stApp { background-color: #f0f2f6; }
    .main-card {
        background-color: white; padding: 40px; border-radius: 20px;
        box-shadow: 0px 10px 40px rgba(0,0,0,0.1);
        max-width: 1000px; margin: auto; margin-top: 50px; border: 1px solid #e0e4e9;
    }
    input, textarea { 
        color: #000 !important; font-weight: 500 !important; 
        background-color: #fff !important; border: 1px solid #dcdcdc !important;
        border-radius: 10px !important; padding: 15px !important;
    }
    div.stButton > button {
        width: 100%; height: 65px; background-color: #4A90E2 !important;
        color: white !important; font-size: 18px !important; font-weight: bold;
        border-radius: 12px; border: none;
    }
    header, footer {visibility: hidden;}
    [data-testid="stHeader"] {display: none;}
    </style>
""", unsafe_allow_html=True)

# --- Anti-Spam Synonym Fixer ---
def spam_cleaner(text):
    words = {
        r"free": "complimentary", r"win": "get", r"money": "funds",
        r"urgent": "important", r"click": "proceed", r"offer": "proposal"
    }
    for p, r in words.items():
        text = re.sub(p, r, text, flags=re.IGNORECASE)
    return text

# --- Session States ---
if 'auth' not in st.session_state: st.session_state.auth = False
if 'sending' not in st.session_state: st.session_state.sending = False
if 'logs' not in st.session_state: st.session_state.logs = {}

# --- Login ---
if not st.session_state.auth:
    col_l, col_m, col_r = st.columns([1, 1.5, 1])
    with col_m:
        st.write("### Login")
        u = st.text_input("User")
        p = st.text_input("Pass", type="password")
        if st.button("Access"):
            if u == "@#2026@#" and p == "@#2026@#":
                st.session_state.auth = True
                st.rerun()
else:
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    
    # 6-Column Layout
    c1, c2 = st.columns(2)
    with c1: s_name = st.text_input("", placeholder="Sender Name (Optional)")
    with c2: s_email = st.text_input("", placeholder="Your Gmail")
    
    c3, c4 = st.columns(2)
    with c3: s_pass = st.text_input("", placeholder="App Password", type="password")
    with c4: subject = st.text_input("", placeholder="Email Subject")
    
    c5, c6 = st.columns(2)
    with c5: body_t = st.text_area("", placeholder="Message Body", height=220)
    with c6: rec_raw = st.text_area("", placeholder="Recipients (one email per line)", height=220)

    # --- Worker Engine ---
    def fast_engine(target_e):
        try:
            target_e = target_e.strip()
            p_body = spam_cleaner(body_t).replace('\n', '<br>')
            
            msg = MIMEMultipart()
            msg['Subject'] = subject
            # display name blank rakha hai taaki sirf email ID dikhe
            msg['From'] = formataddr(("", s_email)) 
            msg['To'] = target_e
            msg['Message-ID'] = make_msgid()
            
            h_tag = f"<div style='display:none;'>Ref-{uuid.uuid4()}</div>"
            msg.attach(MIMEText(f"<html><body>{p_body}{h_tag}</body></html>", 'html'))

            with smtplib.SMTP('smtp.gmail.com', 587, timeout=10) as server:
                server.starttls()
                server.login(s_email, s_pass)
                server.send_message(msg)
            
            st.session_state.logs[s_email].append(time.time())
            return True, target_e
        except Exception as e:
            return False, str(e)

    # --- Buttons ---
    st.write("")
    if st.session_state.sending:
        st.button("⌛ Sending... System Locked", disabled=True)
    else:
        b1, b2 = st.columns(2)
        with b1:
            if st.button("Send All"):
                # Sirf emails extract kar raha hai (no comma/name needed)
                email_list = [l.strip() for l in rec_raw.replace(',', '\n').split('\n') if l.strip()]
                
                now = time.time()
                if s_email not in st.session_state.logs: st.session_state.logs[s_email] = []
                st.session_state.logs[s_email] = [t for t in st.session_state.logs[s_email] if now-t < 3600]
                
                if len(st.session_state.logs[s_email]) >= 28:
                    st.error("❌ Limit reached (28/hr). Change ID. ❌")
                elif not email_list:
                    st.warning("⚠️ Please enter recipient emails!")
                else:
                    st.session_state.sending = True
                    st.rerun()
        with b2:
            if st.button("Logout"):
                st.session_state.auth = False
                st.rerun()

    # --- Parallel Execution ---
    if st.session_state.sending:
        email_list = [l.strip() for l in rec_raw.replace(',', '\n').split('\n') if l.strip()]
        p_bar = st.progress(0)
        status = st.empty()
        success = 0
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
            futures = {ex.submit(fast_engine, em): em for em in email_list}
            for i, f in enumerate(concurrent.futures.as_completed(futures)):
                if len(st.session_state.logs[s_email]) >= 28: break
                ok, res = f.result()
                if ok: success += 1
                p_bar.progress((i+1)/len(email_list))
                status.info(f"🚀 Sent: {i+1}/{len(email_list)} | Success: {success}")

        st.session_state.sending = False
        st.success(f"Mission Complete! {success} Mails Sent.")
        st.balloons()
        time.sleep(2)
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)
