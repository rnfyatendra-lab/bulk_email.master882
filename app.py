import streamlit as st
import smtplib
import time
import concurrent.futures
import re
import uuid
import random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr, make_msgid

# --- Page Setup ---
st.set_page_config(page_title="Safe Console", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    .main-card {
        background-color: white; padding: 30px; border-radius: 12px;
        box-shadow: 0px 4px 20px rgba(0,0,0,0.08);
        max-width: 950px; margin: auto; border: 1px solid #ddd;
    }
    div.stButton > button { width: 100%; height: 60px; font-weight: bold; border-radius: 8px; }
    .send-btn button { background-color: #1a73e8 !important; color: white !important; font-size: 18px !important; }
    .logout-btn button { background-color: #dc3545 !important; color: white !important; }
    header, footer {visibility: hidden;}
    [data-testid="stHeader"] {display: none;}
    </style>
""", unsafe_allow_html=True)

# --- Real Inbox Logic (Spam Bypass) ---
def get_inbox_safe_html(text):
    # Dynamic word variation (Pattern break)
    variations = [
        f"<p>{text.replace('\n', '<br>')}</p>",
        f"<div>{text.replace('\n', '<br>')}</div>",
        f"<span>{text.replace('\n', '<br>')}</span>"
    ]
    main_content = random.choice(variations)
    
    # Invisible unique tracking signature (Inbox Booster)
    unique_id = f"<div style='display:none;font-size:0px;'>{random.random()}</div>"
    
    return f"""
    <html>
        <head><style>body {{font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; color: #333;}}</style></head>
        <body>
            {main_content}
            {unique_id}
        </body>
    </html>
    """

# --- SMTP Worker (High Trust Mode) ---
def send_inbox_mail(recipient, job):
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"{job['s']} {random.randint(100, 999)}" # Random subject suffix
        msg['From'] = formataddr((job['n'], job['e']))
        msg['To'] = recipient
        msg['Message-ID'] = make_msgid(domain='gmail.com')
        
        # Professional Headers for Trust
        msg['X-Mailer'] = "Microsoft Outlook 16.0"
        msg['X-Priority'] = '3 (Normal)'
        msg['Importance'] = 'Normal'
        msg['List-Unsubscribe'] = f"<mailto:{job['e']}?subject=unsubscribe>"
        
        msg.attach(MIMEText(get_inbox_safe_html(job['b']), 'html'))

        with smtplib.SMTP('smtp.gmail.com', 587, timeout=15) as server:
            server.starttls()
            server.login(job['e'], job['p'])
            # Human-like delay
            time.sleep(random.uniform(0.5, 2.0))
            server.send_message(msg)
        return True
    except:
        return False

# --- Session State ---
if 'auth' not in st.session_state: st.session_state.auth = False
if 'is_sending' not in st.session_state: st.session_state.is_sending = False
if 'job_data' not in st.session_state: st.session_state.job_data = None

# --- UI ---
if not st.session_state.auth:
    _, col, _ = st.columns([1, 1, 1])
    with col:
        st.write("### 🔐 Secure Login")
        u = st.text_input("User")
        p = st.text_input("Pass", type="password")
        if st.button("LOGIN"):
            if u == "YATENDRA LODHI" and p == "YATENDRA LODHI":
                st.session_state.auth = True
                st.rerun()
else:
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    with c1: name = st.text_input("Sender Name", key="n")
    with c2: email = st.text_input("Gmail ID", key="e")
    
    c3, c4 = st.columns(2)
    with c3: app_pass = st.text_input("App Password", type="password", key="p")
    with c4: sub = st.text_input("Subject", key="s")
    
    c5, c6 = st.columns(2)
    with c5: msg_body = st.text_area("Body", height=150, key="b")
    with c6: rec_list = st.text_area("Recipients", height=150, key="r")

    if st.session_state.is_sending:
        st.info(f"🚀 Sending from: {st.session_state.job_data['e']} (Processing...)")
        job = st.session_state.job_data
        p_bar = st.progress(0)
        success = 0
        
        

        # Parallel Multi-threading (3 Workers)
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = {executor.submit(send_inbox_mail, em, job): em for em in job['r']}
            for i, f in enumerate(concurrent.futures.as_completed(futures)):
                if f.result() is True: success += 1
                p_bar.progress((i + 1) / len(job['r']))
        
        st.session_state.is_sending = False
        st.session_state.job_data = None
        st.success(f"Final Report: {success} delivered to Inbox.")
        time.sleep(2)
        st.rerun()
            
    else:
        st.write("")
        col_s, col_l = st.columns([0.8, 0.2])
        with col_s:
            st.markdown('<div class="send-btn">', unsafe_allow_html=True)
            if st.button("Send All"):
                targets = list(dict.fromkeys([x.strip() for x in rec_list.replace(',', '\n').split('\n') if x.strip()]))
                if email and app_pass and targets:
                    st.session_state.job_data = {'n': name, 'e': email, 'p': app_pass, 's': sub, 'b': msg_body, 'r': targets}
                    st.session_state.is_sending = True
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        with col_l:
            st.markdown('<div class="logout-btn">', unsafe_allow_html=True)
            if st.button("Logout"):
                st.session_state.auth = False
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
