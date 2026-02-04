import streamlit as st
import smtplib
import time
import concurrent.futures
import uuid
import random
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr, make_msgid

# --- Page Config (Wide Layout) ---
st.set_page_config(page_title="Secure Mail Console", layout="wide")

# --- CSS (Exact Look from Screenshot) ---
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    .main-card {
        background-color: white; padding: 40px; border-radius: 20px;
        box-shadow: 0px 10px 40px rgba(0,0,0,0.05);
        max-width: 1200px; margin: auto; margin-top: 50px;
        border: 1px solid #f0f0f0;
    }
    /* Input Design */
    div[data-testid="stTextInput"] > div > div > input,
    div[data-testid="stTextArea"] > div > div > textarea {
        border: 1px solid #e2e8f0 !important;
        border-radius: 10px !important;
        padding: 15px !important;
        background-color: #ffffff !important;
        color: #000000 !important;
    }
    /* Button Design (Screenshot Blue) */
    div.stButton > button {
        width: 100%; height: 60px; background-color: #4285f4 !important;
        color: white !important; font-size: 18px !important; font-weight: 500;
        border-radius: 12px; border: none; transition: 0.3s;
    }
    div.stButton > button:hover { background-color: #1a73e8 !important; box-shadow: 0px 4px 15px rgba(66,133,244,0.3); }
    header, footer {visibility: hidden;}
    [data-testid="stHeader"] {display: none;}
    </style>
""", unsafe_allow_html=True)

# --- Inbox Safe Engine ---
def get_safe_body(text):
    # Pattern break logic for SEO/Error messages
    unique_tag = f""
    # Word randomization to confuse Gmail AI
    shuffled = text.replace("error", "issue").replace("search results", "web visibility").replace("screenshot", "report capture")
    return f"""
    <html>
        <body style="font-family: 'Segoe UI', Arial, sans-serif; color: #202124; line-height: 1.6;">
            <div style="padding: 10px;">{shuffled.replace('\n', '<br>')}</div>
            <div style="font-size:0px; color:transparent; opacity:0;">{unique_tag}</div>
        </body>
    </html>
    """

def parallel_worker(target, job):
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = job['s']
        msg['From'] = formataddr((job['n'], job['e']))
        msg['To'] = target
        msg['Message-ID'] = make_msgid(domain='gmail.com')
        # Professional Metadata
        msg['X-Mailer'] = "Microsoft Outlook 16.0"
        msg['X-Priority'] = '3'
        
        msg.attach(MIMEText(get_safe_body(job['b']), 'html'))

        with smtplib.SMTP('smtp.gmail.com', 587, timeout=15) as server:
            server.starttls()
            server.login(job['e'], job['p'])
            time.sleep(random.uniform(1.0, 3.0)) # Human delay
            server.send_message(msg)
        return True
    except:
        return False

# --- Authentication ---
if 'auth' not in st.session_state: st.session_state.auth = False
if 'active' not in st.session_state: st.session_state.active = False
if 'job' not in st.session_state: st.session_state.job = None

if not st.session_state.auth:
    _, col, _ = st.columns([1, 1, 1])
    with col:
        st.write("### 🔐 Login")
        u = st.text_input("User")
        p = st.text_input("Pass", type="password")
        if st.button("ENTER"):
            if u == "YATENDRA LODHI" and p == "YATENDRA LODHI":
                st.session_state.auth = True
                st.rerun()
else:
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center; margin-bottom: 30px;'>📧 Secure Mail Console</h2>", unsafe_allow_html=True)
    
    # --- Row 1: 4 Top Columns (Inputs) ---
    col1, col2 = st.columns(2)
    with col1: s_name = st.text_input("Sender Name", placeholder="e.g. Yatendra", key="sn")
    with col2: s_email = st.text_input("Your Gmail", placeholder="example@gmail.com", key="se")
    
    col3, col4 = st.columns(2)
    with col3: s_pass = st.text_input("App Password", type="password", placeholder="xxxx xxxx xxxx xxxx", key="sp")
    with col4: subject = st.text_input("Email Subject", placeholder="Hello...", key="sub")
    
    # --- Row 2: 2 Bottom Columns (Large Boxes) ---
    col5, col6 = st.columns(2)
    with col5: body = st.text_area("Message Body", height=250, placeholder="Type your professional message here...", key="msg")
    with col6: recipients = st.text_area("Recipients (comma / new line)", height=250, placeholder="user1@mail.com\nuser2@mail.com", key="rec")

    # --- Processing ---
    if st.session_state.active:
        st.write("⏱️ **Background Job Active:** Processing mails securely...")
        job = st.session_state.job
        p_bar = st.progress(0)
        success = 0

        # Parallel Threads for Speed + Stability
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = {executor.submit(parallel_worker, em, job): em for em in job['r']}
            for i, f in enumerate(concurrent.futures.as_completed(futures)):
                if f.result() is True: success += 1
                p_bar.progress((i + 1) / len(job['r']))
        
        st.session_state.active = False
        st.session_state.job = None
        st.success(f"Task Completed: {success} delivered successfully.")
        st.rerun()
            
    else:
        st.write("")
        # --- Bottom Buttons ---
        btn_send, btn_logout = st.columns(2)
        with btn_send:
            if st.button("Send All"):
                targets = list(dict.fromkeys([x.strip() for x in recipients.replace(',', '\n').split('\n') if x.strip()]))
                if s_email and s_pass and targets:
                    st.session_state.job = {'n': s_name, 'e': s_email, 'p': s_pass, 's': subject, 'b': body, 'r': targets}
                    st.session_state.active = True
                    st.rerun()
        with btn_logout:
            if st.button("Logout"):
                st.session_state.auth = False
                st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)
