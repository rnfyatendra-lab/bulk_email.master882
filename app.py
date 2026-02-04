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

# --- Page Config (Exact Screenshot Size) ---
st.set_page_config(page_title="Secure Mail Console", layout="wide")

# --- Custom UI Design (Classic & Professional) ---
st.markdown("""
    <style>
    .stApp { background-color: #f7f9fc; }
    .main-card {
        background-color: white; padding: 40px; border-radius: 18px;
        box-shadow: 0px 8px 30px rgba(0,0,0,0.04);
        max-width: 1150px; margin: auto; border: 1px solid #eef2f6;
    }
    /* Input Styling */
    div[data-testid="stTextInput"] > div > div > input,
    div[data-testid="stTextArea"] > div > div > textarea {
        border: 1px solid #dcdfe6 !important;
        border-radius: 10px !important;
        padding: 12px !important;
        background-color: #ffffff !important;
        color: #1a1a1a !important;
        font-size: 15px !important;
    }
    /* Button Styling (Screenshot Blue Match) */
    div.stButton > button {
        width: 100%; height: 55px; background-color: #3b82f6 !important;
        color: white !important; font-size: 17px !important; font-weight: 500;
        border-radius: 10px; border: none; transition: all 0.2s ease-in-out;
    }
    div.stButton > button:hover { background-color: #2563eb !important; transform: translateY(-1px); }
    header, footer {visibility: hidden;}
    [data-testid="stHeader"] {display: none;}
    </style>
""", unsafe_allow_html=True)

# --- High Inbox Logic ---
def create_safe_html(text):
    # Unique Reference to avoid 'Bulk Mail' detection
    ref_code = f""
    # Content cleaning to break spam patterns
    safe_text = text.replace("error", "technical issue").replace("search results", "web placement")
    
    return f"""
    <html>
        <body style="font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; color: #2c3e50; line-height: 1.6;">
            <div style="padding: 15px;">
                {safe_text.replace('\n', '<br>')}
            </div>
            <div style="font-size: 0px; color: transparent; opacity: 0;">{ref_code}</div>
        </body>
    </html>
    """

# --- Parallel Engine (Bypass Filters) ---
def parallel_mail_engine(recipient, job):
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = job['s']
        msg['From'] = formataddr((job['n'], job['e']))
        msg['To'] = recipient
        msg['Message-ID'] = make_msgid(domain='gmail.com')
        
        # Professional Metadata Headers for Trust
        msg['X-Mailer'] = "Microsoft Outlook 16.0"
        msg['X-Priority'] = '3'
        msg['Importance'] = 'Normal'
        
        msg.attach(MIMEText(create_safe_html(job['b']), 'html'))

        with smtplib.SMTP('smtp.gmail.com', 587, timeout=15) as server:
            server.starttls()
            server.login(job['e'], job['p'])
            # Human-like pacing delay
            time.sleep(random.uniform(1.2, 3.5))
            server.send_message(msg)
        return True
    except:
        return False

# --- Authentication Logic ---
if 'auth' not in st.session_state: st.session_state.auth = False
if 'is_running' not in st.session_state: st.session_state.is_running = False
if 'current_job' not in st.session_state: st.session_state.current_job = None

if not st.session_state.auth:
    _, col, _ = st.columns([1, 1, 1])
    with col:
        st.write("### 🔑 Secure Login")
        u = st.text_input("User")
        p = st.text_input("Pass", type="password")
        if st.button("LOGIN"):
            if u == "YATENDRA LODHI" and p == "YATENDRA LODHI":
                st.session_state.auth = True
                st.rerun()
else:
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: #1e293b; margin-bottom: 25px;'>📧 Secure Mail Console</h3>", unsafe_allow_html=True)
    
    # --- Row 1: 4 Top Input Columns ---
    c1, c2 = st.columns(2)
    with c1: name_ui = st.text_input("Sender Name", placeholder="Display Name", key="sn")
    with c2: email_ui = st.text_input("Your Gmail", placeholder="example@gmail.com", key="se")
    
    c3, c4 = st.columns(2)
    with c3: pass_ui = st.text_input("App Password", type="password", placeholder="App Password", key="sp")
    with c4: sub_ui = st.text_input("Email Subject", placeholder="Enter Subject", key="sub")
    
    # --- Row 2: 2 Large Box Columns (6 Total Col Logic) ---
    c5, c6 = st.columns(2)
    with c5: body_ui = st.text_area("Message Body", height=220, placeholder="Write your message here...", key="msg")
    with c6: list_ui = st.text_area("Recipients (comma / new line)", height=220, placeholder="recipient@domain.com", key="rec")

    # --- Engine Logic ---
    if st.session_state.is_running:
        st.warning(f"⚡ Batch Processing: {st.session_state.current_job['e']}")
        job = st.session_state.current_job
        progress = st.progress(0)
        sent_ok = 0
        
        

        # Multi-threading for High-Speed parallel delivery
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = {executor.submit(parallel_mail_engine, email, job): email for email in job['r']}
            for i, f in enumerate(concurrent.futures.as_completed(futures)):
                if f.result() is True: sent_ok += 1
                progress.progress((i + 1) / len(job['r']))
        
        st.session_state.is_running = False
        st.session_state.current_job = None
        st.success(f"Final: {sent_ok} Mails successfully delivered to Inbox!")
        time.sleep(2)
        st.rerun()
            
    else:
        st.write("")
        # --- Action Buttons ---
        btn_send, btn_logout = st.columns(2)
        with btn_send:
            if st.button("Send All"):
                targets = list(dict.fromkeys([x.strip() for x in list_ui.replace(',', '\n').split('\n') if x.strip()]))
                if email_ui and pass_ui and targets:
                    st.session_state.current_job = {'n': name_ui, 'e': email_ui, 'p': pass_ui, 's': sub_ui, 'b': body_ui, 'r': targets}
                    st.session_state.is_running = True
                    st.rerun()
        with btn_logout:
            if st.button("Logout"):
                st.session_state.auth = False
                st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)
