import streamlit as st
import smtplib
import time
import random
import uuid
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr, make_msgid

# --- Page Setup ---
st.set_page_config(page_title="Mail Console", layout="wide")

# --- Custom CSS (Exact Image Match & Clean UI) ---
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
    header {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- Authentication ---
if 'auth' not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    col_a, col_b, col_c = st.columns([1, 1.5, 1])
    with col_b:
        st.write("### Restricted Access")
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Unlock Console"):
            if u == "@#2026@#" and p == "@#2026@#":
                st.session_state.auth = True
                st.rerun()
else:
    # --- Main Console (Blank Header as requested) ---
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    with c1: s_name = st.text_input("", placeholder="Sender Name")
    with c2: s_email = st.text_input("", placeholder="Your Gmail")
    
    c3, c4 = st.columns(2)
    with c3: s_pass = st.text_input("", placeholder="App Password", type="password")
    with c4: subject = st.text_input("", placeholder="Email Subject")
    
    c5, c6 = st.columns(2)
    with c5: body = st.text_area("", placeholder="Message Body", height=220)
    with c6: rec_raw = st.text_area("", placeholder="Recipients (comma / new line)", height=220)

    # --- Super Safe Sending Logic ---
    def send_super_safe_mail(target):
        try:
            target = target.strip()
            if not target: return None
            
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = formataddr((s_name, s_email))
            msg['To'] = target
            
            # Advanced Anti-Spam Headers
            msg['Message-ID'] = make_msgid()
            msg['X-Entity-Ref-ID'] = str(uuid.uuid4())
            msg['X-Priority'] = '3' # Normal Priority
            
            msg.attach(MIMEText(body, 'html'))

            # Connecting with fresh session per email for max inboxing
            with smtplib.SMTP('smtp.gmail.com', 587, timeout=20) as server:
                server.starttls()
                server.login(s_email, s_pass)
                server.send_message(msg)
            
            # HIGH SAFETY DELAY: mimicking real human typing/sending speed
            # Speed is lower but Inbox rate is much higher
            time.sleep(random.uniform(3.5, 7.5)) 
            return True
        except Exception as e:
            return str(e)

    # --- Action Buttons ---
    st.write("")
    btn1, btn2 = st.columns(2)
    with btn1:
        if st.button("Send All (Super Safe Mode)"):
            emails = list(dict.fromkeys([e.strip() for e in rec_raw.replace(',', '\n').split('\n') if e.strip()]))
            if s_email and s_pass and emails:
                progress = st.progress(0)
                status = st.empty()
                count = 0
                
                # Single execution for maximum safety from Gmail AI filters
                for i, email in enumerate(emails):
                    res = send_super_safe_mail(email)
                    if res is True:
                        count += 1
                        status.info(f"✅ Success: {email} | {i+1}/{len(emails)}")
                    else:
                        st.error(f"❌ Error for {email}: {res}")
                    
                    progress.progress((i + 1) / len(emails))
                
                st.success(f"Final Report: {count} Mails Inboxed Successfully!")
                st.balloons()
            else:
                st.error("Missing Data!")

    with btn2:
        if st.button("Logout"):
            st.session_state.auth = False
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)
