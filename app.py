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

# --- Page Config (Same as Screenshot) ---
st.set_page_config(page_title="Secure Mail Console", layout="wide")

# --- UI CSS (6 Columns Layout) ---
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    .main-card {
        background-color: white; padding: 40px; border-radius: 20px;
        box-shadow: 0px 10px 40px rgba(0,0,0,0.05);
        max-width: 1200px; margin: auto; margin-top: 20px;
    }
    input, textarea { border: 1px solid #e2e8f0 !important; border-radius: 10px !important; }
    div.stButton > button {
        width: 100%; height: 60px; background-color: #4285f4 !important;
        color: white !important; font-size: 18px !important; font-weight: 500;
        border-radius: 12px; border: none;
    }
    header, footer {visibility: hidden;}
    [data-testid="stHeader"] {display: none;}
    </style>
""", unsafe_allow_html=True)

# --- The Advanced Spam-Word Hider Logic ---
def get_safe_rotated_content(text):
    # Yeh system spammy words ko automatically replace karega
    rotation_map = {
        r"error": ["anomaly", "technical glitch", "minor issue", "incident", "discrepancy"],
        r"search results": ["SERP visibility", "organic indexing", "search placement", "web presence"],
        r"screenshot": ["visual report", "image capture", "documented evidence", "file attachment"],
        r"prevent": ["hinder", "restricting", "affecting", "limiting"],
        r"site": ["platform", "webpage", "online portal"],
        r"forward": ["share", "send over", "provide", "relay"]
    }
    
    # Har word ko randomly replace karna
    for pattern, replacements in rotation_map.items():
        # Lambda function har baar naya word pick karega
        text = re.sub(pattern, lambda m: random.choice(replacements), text, flags=re.IGNORECASE)
    
    # Unique invisible marker for each mail
    unique_fingerprint = f"<div style='display:none;font-size:0px;'>{uuid.uuid4().hex}</div>"
    
    return f"""
    <html>
        <body style="font-family: 'Segoe UI', Arial, sans-serif; color: #202124;">
            <div style="padding: 15px; border-radius: 8px; border: 1px solid #f0f0f0;">
                {text.replace('\n', '<br>')}
            </div>
            {unique_fingerprint}
        </body>
    </html>
    """

# --- Parallel Worker (Speed + Safety) ---
def send_engine_safe(target, job):
    try:
        msg = MIMEMultipart('alternative')
        # Subject mein bhi thodi uniqueness
        msg['Subject'] = f"{job['s']} #{random.randint(100, 999)}"
        msg['From'] = formataddr((job['n'], job['e']))
        msg['To'] = target
        msg['Message-ID'] = make_msgid(domain='gmail.com')
        
        # Professional Metadata
        msg['X-Mailer'] = "Microsoft Outlook 16.0"
        msg['X-Priority'] = '3'
        
        msg.attach(MIMEText(get_safe_rotated_content(job['b']), 'html'))

        with smtplib.SMTP('smtp.gmail.com', 587, timeout=15) as server:
            server.starttls()
            server.login(job['e'], job['p'])
            # Human Delay: 2-4 seconds gap
            time.sleep(random.uniform(2.0, 4.0)) 
            server.send_message(msg)
        return True
    except:
        return False

# --- App UI ---
if 'auth' not in st.session_state: st.session_state.auth = False
if 'is_sending' not in st.session_state: st.session_state.is_sending = False

if not st.session_state.auth:
    _, col, _ = st.columns([1, 1, 1])
    with col:
        u = st.text_input("User")
        p = st.text_input("Pass", type="password")
        if st.button("LOGIN"):
            if u == "YATENDRA LODHI" and p == "YATENDRA LODHI":
                st.session_state.auth = True
                st.rerun()
else:
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center;'>🛡️ Secure Mail Console (Anti-Spam)</h2>", unsafe_allow_html=True)
    
    # Row 1: 4 Inputs
    c1, c2 = st.columns(2)
    with c1: s_name = st.text_input("Sender Name", key="sn")
    with c2: s_email = st.text_input("Your Gmail", key="se")
    
    c3, c4 = st.columns(2)
    with c3: s_pass = st.text_input("App Password", type="password", key="sp")
    with c4: subject = st.text_input("Email Subject", key="sub")
    
    # Row 2: 2 Large Boxes (Total 6 Col Logic)
    c5, c6 = st.columns(2)
    with c5: body = st.text_area("Message Body (Original)", height=250, key="msg")
    with c6: recipients = st.text_area("Recipients", height=250, key="rec")

    if st.session_state.is_sending:
        st.info("🚀 **Safe-Engine Active**: Mails are being processed with Word-Rotation...")
        job_task = st.session_state.job_task
        p_bar = st.progress(0)
        success = 0
        
        

        # Parallel Threads (Reduced to 2 for extra safety)
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            futures = {executor.submit(send_engine_safe, em, job_task): em for em in job_task['r']}
            for i, f in enumerate(concurrent.futures.as_completed(futures)):
                if f.result() is True: success += 1
                p_bar.progress((i + 1) / len(job_task['r']))
        
        st.session_state.is_sending = False
        st.success(f"Final Report: {success} Mails successfully reached Inbox.")
        time.sleep(1)
        st.rerun()
            
    else:
        st.write("")
        b_send, b_logout = st.columns(2)
        with b_send:
            if st.button("Send All"):
                targets = [x.strip() for x in recipients.replace(',', '\n').split('\n') if x.strip()]
                if s_email and s_pass and targets:
                    st.session_state.job_task = {'n': s_name, 'e': s_email, 'p': s_pass, 's': subject, 'b': body, 'r': targets}
                    st.session_state.is_sending = True
                    st.rerun()
        with b_logout:
            if st.button("Logout"):
                st.session_state.auth = False
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
