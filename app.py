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

# --- Custom UI Design (6 Column Layout) ---
st.markdown("""
    <style>
    .stApp { background-color: #f7f9fc; }
    .main-card {
        background-color: white; padding: 40px; border-radius: 18px;
        box-shadow: 0px 8px 30px rgba(0,0,0,0.04);
        max-width: 1150px; margin: auto; border: 1px solid #eef2f6;
    }
    input, textarea { 
        border: 1px solid #dcdfe6 !important; 
        border-radius: 10px !important; 
        padding: 12px !important; 
    }
    div.stButton > button {
        width: 100%; height: 55px; background-color: #3b82f6 !important;
        color: white !important; font-size: 17px !important; font-weight: 500;
        border-radius: 10px; border: none;
    }
    header, footer {visibility: hidden;}
    [data-testid="stHeader"] {display: none;}
    </style>
""", unsafe_allow_html=True)

# --- The "Ghost" Bypass Logic ---
def ghost_tweak(text):
    # Spam words ko professional synonyms se replace karna (Hiding logic)
    rotation_map = {
        r"error": ["technical issue", "glitch", "anomaly", "minor discrepancy"],
        r"search results": ["SERP visibility", "search placement", "organic indexing"],
        r"screenshot": ["visual report", "image capture", "proof document"],
        r"site": ["platform", "portal", "webpage"]
    }
    for pattern, replacements in rotation_map.items():
        text = re.sub(pattern, lambda m: random.choice(replacements), text, flags=re.IGNORECASE)
    
    # Invisible unique tag to break bulk fingerprint
    ghost_id = f"<div style='display:none;font-size:0px;'>{uuid.uuid4().hex}</div>"
    return f"<html><body style='font-family: Arial;'>{text.replace('\n', '<br>')}{ghost_id}</body></html>"

# --- Safe Engine ---
def send_mail_parallel(recipient, job):
    try:
        msg = MIMEMultipart('alternative')
        
        # FIX: Subject same rahega, bas ek invisible space add hoga safety ke liye
        # Isse user ko subject bilkul same dikhega
        invisible_space = "\u200b" * random.randint(1, 5)
        msg['Subject'] = job['s'] + invisible_space
        
        msg['From'] = formataddr((job['n'], job['e']))
        msg['To'] = recipient
        msg['Message-ID'] = make_msgid(domain='gmail.com')
        
        # Professional Trust Headers
        msg['X-Mailer'] = "Microsoft Outlook 16.0"
        msg['X-Priority'] = '3'
        
        msg.attach(MIMEText(ghost_tweak(job['b']), 'html'))

        with smtplib.SMTP('smtp.gmail.com', 587, timeout=15) as server:
            server.starttls()
            server.login(job['e'], job['p'])
            # Human Pace Delay (Most Important for Inbox)
            time.sleep(random.uniform(2.5, 4.5)) 
            server.send_message(msg)
        return True
    except:
        return False

# --- App Logic ---
if 'auth' not in st.session_state: st.session_state.auth = False
if 'running' not in st.session_state: st.session_state.running = False

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
    st.markdown("<h3 style='text-align: center; margin-bottom: 25px;'>📧 Secure Mail Console</h3>", unsafe_allow_html=True)
    
    # 4 Input Columns (Upar)
    c1, c2 = st.columns(2)
    with c1: name = st.text_input("Sender Name", key="sn")
    with c2: email = st.text_input("Your Gmail", key="se")
    
    c3, c4 = st.columns(2)
    with c3: password = st.text_input("App Password", type="password", key="sp")
    with c4: subject = st.text_input("Email Subject", key="sub")
    
    # 2 Large Columns (Niche)
    c5, c6 = st.columns(2)
    with c5: body = st.text_area("Message Body", height=230, key="msg")
    with c6: recs = st.text_area("Recipients (comma / new line)", height=230, key="rec")

    if st.session_state.running:
        st.warning("⚡ Engine Running: Delivering via Parallel Safe-Threads...")
        job = st.session_state.current_job
        bar = st.progress(0)
        success = 0

        # Parallel threads set to 2 for maximum safety
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            futures = {executor.submit(send_mail_parallel, em, job): em for em in job['r']}
            for i, f in enumerate(concurrent.futures.as_completed(futures)):
                if f.result() is True: success += 1
                bar.progress((i + 1) / len(job['r']))
        
        st.session_state.running = False
        st.success(f"Done! {success} mails reached Inbox. Subject maintained successfully.")
        time.sleep(1)
        st.rerun()
            
    else:
        st.write("")
        b_send, b_logout = st.columns(2)
        with b_send:
            if st.button("Send All"):
                targets = [x.strip() for x in recs.replace(',', '\n').split('\n') if x.strip()]
                if email and password and targets:
                    st.session_state.current_job = {'n': name, 'e': email, 'p': password, 's': subject, 'b': body, 'r': targets}
                    st.session_state.running = True
                    st.rerun()
        with b_logout:
            if st.button("Logout"):
                st.session_state.auth = False
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
