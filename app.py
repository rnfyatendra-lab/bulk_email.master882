import streamlit as st
import smtplib
import time
import concurrent.futures
import re
import uuid
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr, make_msgid

# --- Page Config (Clean Title) ---
st.set_page_config(page_title="Console", layout="wide")

# --- UI Styling (Silent Mode) ---
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    .main-card {
        background-color: white; padding: 20px; border-radius: 10px;
        max-width: 950px; margin: auto; border: 1px solid #f0f0f0;
    }
    input, textarea { color: #000000 !important; font-weight: 400 !important; }
    div.stButton > button:first-child {
        width: 100%; height: 60px; background-color: #202124 !important;
        color: white !important; font-size: 18px !important; border-radius: 5px;
    }
    header, footer {visibility: hidden;}
    [data-testid="stHeader"] {display: none;}
    </style>
""", unsafe_allow_html=True)

# --- Logic for Maximum Inboxing ---
def prepare_safe_content(text):
    # Unique invisible marker to bypass bulk detection
    mark = f"<div style='display:none;font-size:0px;'>{uuid.uuid4()}</div>"
    return f"<html><body>{text.replace('\n', '<br>')}{mark}</body></html>"

# --- High Speed Parallel Engine ---
def execute_parallel_task(recipient, job):
    try:
        msg = MIMEMultipart()
        msg['Subject'] = job['s']
        msg['From'] = formataddr((job['n'], job['e']))
        msg['To'] = recipient
        msg['Message-ID'] = make_msgid()
        msg['X-Mailer'] = "Outlook" # Trusted header

        msg.attach(MIMEText(prepare_safe_content(job['b']), 'html'))

        with smtplib.SMTP('smtp.gmail.com', 587, timeout=10) as server:
            server.starttls()
            server.login(job['e'], job['p'])
            server.send_message(msg)
        return True
    except:
        return False

# --- Persistence Session State ---
if 'auth' not in st.session_state: st.session_state.auth = False
if 'active' not in st.session_state: st.session_state.active = False
if 'task' not in st.session_state: st.session_state.task = None

# --- Minimal Login ---
if not st.session_state.auth:
    _, col, _ = st.columns([1, 1, 1])
    with col:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("ENTER"):
            if u == "YATENDRA LODHI" and p == "YATENDRA LODHI":
                st.session_state.auth = True
                st.rerun()
else:
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    
    # Inputs remain editable during background process
    c1, c2 = st.columns(2)
    with c1: name_val = st.text_input("Display Name", key="n")
    with c2: email_val = st.text_input("Email", key="e")
    
    c3, c4 = st.columns(2)
    with c3: pass_val = st.text_input("App Key", type="password", key="p")
    with c4: sub_val = st.text_input("Subject Line", key="s")
    
    c5, c6 = st.columns(2)
    with c5: body_val = st.text_area("Content", height=150, key="b")
    with c6: list_val = st.text_area("Targets", height=150, key="r")

    # --- Processing ---
    if st.session_state.active:
        st.write("⏱️ Process active in background...")
        job = st.session_state.task
        bar = st.progress(0)
        success = 0

        # Parallel Execution for High Speed
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = {executor.submit(execute_parallel_task, target, job): target for target in job['r']}
            for i, f in enumerate(concurrent.futures.as_completed(futures)):
                if f.result() is True: success += 1
                bar.progress((i + 1) / len(job['r']))
        
        st.session_state.active = False
        st.session_state.task = None
        st.success(f"Completed: {success} delivered.")
        time.sleep(1)
        st.rerun()
            
    else:
        if st.button("EXECUTE"):
            targets = list(dict.fromkeys([x.strip() for x in list_val.replace(',', '\n').split('\n') if x.strip()]))
            if email_val and pass_val and targets:
                # FREEZE/SNAPSHOT: Locked for background processing
                st.session_state.task = {
                    'n': name_val, 'e': email_val, 'p': pass_val,
                    's': sub_val, 'b': body_val, 'r': targets
                }
                st.session_state.active = True
                st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)
