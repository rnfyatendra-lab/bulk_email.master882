import streamlit as st
import smtplib
import time
import random
import uuid
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr, make_msgid

# --- Page Setup ---
st.set_page_config(page_title="Console", layout="wide")

# --- Exact UI Match CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #f0f2f6; }
    .main-card {
        background-color: white; padding: 40px; border-radius: 20px;
        box-shadow: 0px 10px 40px rgba(0,0,0,0.1);
        max-width: 1000px; margin: 50px auto; border: 1px solid #e0e4e9;
    }
    input, textarea { 
        color: #333 !important; 
        background-color: #ffffff !important; 
        border: 1px solid #dcdcdc !important;
        border-radius: 10px !important;
        padding: 12px !important;
    }
    div.stButton > button {
        width: 100%; height: 55px; font-size: 18px !important;
        border-radius: 12px; border: none; font-weight: 500;
        background-color: #4A90E2 !important; color: white !important;
    }
    header, footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- Login Logic ---
if 'auth' not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    col_l, col_m, col_r = st.columns([1, 1.5, 1])
    with col_m:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Unlock"):
            if u == "@#2026@#" and p == "@#2026@#":
                st.session_state.auth = True
                st.rerun()
else:
    # --- Main Dashboard (No Header) ---
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    
    # Row 1
    c1, c2 = st.columns(2)
    with c1: s_name = st.text_input("", placeholder="Sender Name")
    with c2: s_email = st.text_input("", placeholder="Your Gmail")
    
    # Row 2
    c3, c4 = st.columns(2)
    with c3: s_pass = st.text_input("", placeholder="App Password", type="password")
    with c4: subject = st.text_input("", placeholder="Email Subject")
    
    # Row 3 (6-Column grid equivalent)
    c5, c6 = st.columns(2)
    with c5: body = st.text_area("", placeholder="Message Body", height=220)
    with c6: rec_raw = st.text_area("", placeholder="Recipients (comma / new line)", height=220)

    # --- Secure Engine ---
    def send_one_by_one(target):
        try:
            target = target.strip()
            if not target: return None
            
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = formataddr((s_name, s_email))
            msg['To'] = target
            
            # Anti-Spam Professional Headers
            msg['Message-ID'] = make_msgid()
            msg['X-Entity-ID'] = str(uuid.uuid4())
            msg['List-Unsubscribe'] = f'<mailto:{s_email}>'
            
            msg.attach(MIMEText(body, 'html'))

            with smtplib.SMTP('smtp.gmail.com', 587, timeout=25) as server:
                server.starttls()
                server.login(s_email, s_pass)
                server.send_message(msg)
            
            # CRITICAL: Randomized delay for Inbox reputation
            time.sleep(random.uniform(5.2, 9.8)) 
            return True
        except Exception as e:
            return str(e)

    # --- Buttons ---
    st.write("")
    b_send, b_out = st.columns(2)
    with b_send:
        if st.button("Send All (Safe Mode)"):
            emails = list(dict.fromkeys([e.strip() for e in rec_raw.replace(',', '\n').split('\n') if e.strip()]))
            if s_email and s_pass and emails:
                p_bar = st.progress(0)
                status = st.empty()
                success = 0
                
                # Processing one-by-one is the ONLY way to stay 100% safe
                for i, email in enumerate(emails):
                    res = send_one_by_one(email)
                    if res is True:
                        success += 1
                        status.success(f"Inboxed: {email} ({i+1}/{len(emails)})")
                    else:
                        status.error(f"Blocked: {email} | Error: {res}")
                    
                    p_bar.progress((i + 1) / len(emails))
                
                st.balloons()
                st.write(f"### Final Result: {success} Inboxed Successfully")
            else:
                st.error("Fields missing!")

    with b_out:
        if st.button("Logout"):
            st.session_state.auth = False
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)
