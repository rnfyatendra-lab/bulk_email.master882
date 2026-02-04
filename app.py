import streamlit as st
import smtplib
import time
import concurrent.futures
import uuid
import random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr, make_msgid

# --- Page Config ---
st.set_page_config(page_title="Inbox King Console", layout="wide")

# --- UI Styling (6 Columns Style) ---
st.markdown("""
    <style>
    .stApp { background-color: #f4f7f6; }
    .main-card {
        background-color: white; padding: 40px; border-radius: 15px;
        box-shadow: 0px 5px 25px rgba(0,0,0,0.07);
        max-width: 1100px; margin: auto; margin-top: 30px;
    }
    input, textarea { border-radius: 8px !important; border: 1px solid #ddd !important; }
    div.stButton > button {
        width: 100%; height: 55px; background-color: #1a73e8 !important;
        color: white !important; font-weight: bold; border-radius: 10px; border: none;
    }
    header, footer {visibility: hidden;}
    [data-testid="stHeader"] {display: none;}
    </style>
""", unsafe_allow_html=True)

# --- The Inbox Logic ---
def get_clean_html(original_text):
    # Bilkul same text rahega, bas ek invisible UID last mein
    # Jo Google ke "Duplicate Content" filter ko bypass karega
    ghost_id = f""
    return f"<html><body style='font-family: Arial, sans-serif;'>{original_text.replace('\n', '<br>')}{ghost_id}</body></html>"

def send_inbox_engine(recipient, job):
    try:
        msg = MIMEMultipart('alternative')
        # Exact Subject + Invisible space
        msg['Subject'] = job['s'] + ("\u200b" * random.randint(1, 10))
        msg['From'] = formataddr((job['n'], job['e']))
        msg['To'] = recipient
        msg['Message-ID'] = make_msgid(domain='gmail.com')
        
        # Essential Headers for Inbox Delivery
        msg['X-Mailer'] = "Microsoft Outlook 16.0"
        msg['X-Priority'] = '3'
        
        msg.attach(MIMEText(get_clean_html(job['b']), 'html'))

        with smtplib.SMTP('smtp.gmail.com', 587, timeout=15) as server:
            server.starttls()
            server.login(job['e'], job['p'])
            
            # Natural Timing (Bypasses Bot-Detection)
            time.sleep(random.uniform(2.0, 4.0)) 
            
            server.send_message(msg)
        return True
    except:
        return False

# --- Auth & UI ---
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
    st.markdown("<h3 style='text-align: center;'>📧 Secure Mail Launcher</h3>", unsafe_allow_html=True)
    
    # Row 1: 4 Inputs
    c1, c2 = st.columns(2)
    with c1: name = st.text_input("Sender Name", key="sn")
    with c2: email = st.text_input("Your Gmail", key="se")
    
    c3, c4 = st.columns(2)
    with c3: password = st.text_input("App Password", type="password", key="sp")
    with c4: subject = st.text_input("Email Subject", key="sub")
    
    # Row 2: 2 Boxes
    c5, c6 = st.columns(2)
    with c5: body = st.text_area("Message Body", height=230, key="msg")
    with c6: recs = st.text_area("Recipients", height=230, key="rec")

    if st.session_state.is_sending:
        st.info("🚀 Delivering to Inbox... (Parallel Safe Mode)")
        job = st.session_state.current_job
        bar = st.progress(0)
        success = 0
        
        

        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = {executor.submit(send_inbox_engine, em, job): em for em in job['r']}
            for i, f in enumerate(concurrent.futures.as_completed(futures)):
                if f.result() is True: success += 1
                bar.progress((i + 1) / len(job['r']))
        
        st.session_state.is_sending = False
        st.success(f"Task Finished! {success} mails reached Inbox.")
        st.rerun()
            
    else:
        st.write("")
        b_send, b_logout = st.columns(2)
        with b_send:
            if st.button("Send All"):
                targets = [x.strip() for x in recs.replace(',', '\n').split('\n') if x.strip()]
                if email and password and targets:
                    st.session_state.current_job = {'n': name, 'e': email, 'p': password, 's': subject, 'b': body, 'r': targets}
                    st.session_state.is_sending = True
                    st.rerun()
        with b_logout:
            if st.button("Logout"):
                st.session_state.auth = False
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
