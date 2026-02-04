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

# --- Page Config ---
st.set_page_config(page_title="Console Professional", layout="wide")

# --- UI Styling ---
st.markdown("""
    <style>
    .stApp { background-color: #f4f7f9; }
    .main-card {
        background-color: white; padding: 30px; border-radius: 12px;
        box-shadow: 0px 4px 20px rgba(0,0,0,0.05);
        max-width: 1100px; margin: auto; border: 1px solid #e1e4e8;
    }
    div.stButton > button { width: 100%; height: 50px; border-radius: 8px; font-weight: bold; }
    .send-btn button { background-color: #1a73e8 !important; color: white !important; }
    header, footer {visibility: hidden;}
    [data-testid="stHeader"] {display: none;}
    </style>
""", unsafe_allow_html=True)

# --- Anti-Spam Logic: Word Shuffling ---
def sanitize_content(text):
    # Spammy words ko professional synonyms se replace karna (Automatic)
    synonyms = {
        r"error": ["issue", "anomaly", "glitch", "incident"],
        r"prevent": ["hinder", "restricting", "blocking"],
        r"search results": ["SERP visibility", "search indexing", "web presence"],
        r"screenshot": ["visual report", "capture", "documentation"],
        r"email": ["this channel", "direct message", "correspondence"]
    }
    
    for word, replacements in synonyms.items():
        text = re.sub(word, random.choice(replacements), text, flags=re.IGNORECASE)
    
    # Invisible unique tracking ID to break pattern
    fingerprint = f"<div style='display:none;font-size:0px;'>{uuid.uuid4().hex}</div>"
    return f"<html><body style='font-family: Arial; line-height:1.6;'>{text.replace('\n', '<br>')}{fingerprint}</body></html>"

# --- Pro Sending Engine ---
def execute_safe_send(target, job):
    try:
        # Template & Subject Selection
        bodies = [b for b in [job['b1'], job['b2'], job['b3']] if b.strip()]
        subjects = [s for s in [job['s1'], job['s2'], job['s3']] if s.strip()]
        
        final_body = random.choice(bodies) if bodies else job['b1']
        final_subject = random.choice(subjects) if subjects else job['s1']

        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"{final_subject} - {random.randint(100, 999)}"
        msg['From'] = formataddr((job['n'], job['e']))
        msg['To'] = target
        msg['Message-ID'] = make_msgid(domain='gmail.com')
        
        # Adding Corporate Trust Headers
        msg['X-Mailer'] = "Microsoft Outlook 16.0"
        msg['X-Priority'] = '3'
        
        msg.attach(MIMEText(sanitize_content(final_body), 'html'))

        with smtplib.SMTP('smtp.gmail.com', 587, timeout=12) as server:
            server.starttls()
            server.login(job['e'], job['p'])
            # Human-like delay (Bypass Bot detection)
            time.sleep(random.uniform(1.0, 3.0))
            server.send_message(msg)
        return True
    except:
        return False

# --- Auth ---
if 'auth' not in st.session_state: st.session_state.auth = False
if 'is_running' not in st.session_state: st.session_state.is_running = False
if 'job_task' not in st.session_state: st.session_state.job_task = None

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
    
    # UI Inputs
    c1, c2, c3 = st.columns(3)
    with c1: name_ui = st.text_input("Display Name", key="n")
    with c2: email_ui = st.text_input("Sender Gmail", key="e")
    with c3: pass_ui = st.text_input("App Password", type="password", key="p")
    
    st.write("---")
    st.write("🔄 **Subject Rotation (Different Subjects for Each Mail)**")
    s1, s2, s3 = st.columns(3)
    with s1: sub1 = st.text_input("Subject 1", key="s1")
    with s2: sub2 = st.text_input("Subject 2", key="s2")
    with sub3: sub3 = st.text_input("Subject 3", key="s3")

    st.write("📝 **Professional Templates (Anti-Spam Active)**")
    b1, b2, b3 = st.columns(3)
    with b1: body1 = st.text_area("Template A", height=200, key="b1")
    with b2: body2 = st.text_area("Template B", height=200, key="b2")
    with b3: body3 = st.text_area("Template C", height=200, key="b3")
    
    list_ui = st.text_area("Recipients List", height=100, key="r")

    if st.session_state.is_running:
        st.info(f"⚡ Secure Sending Active from: {st.session_state.job_task['e']}")
        job = st.session_state.job_task
        p_bar = st.progress(0)
        success = 0
        
        

        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = {executor.submit(execute_safe_send, em, job): em for em in job['r']}
            for i, f in enumerate(concurrent.futures.as_completed(futures)):
                if f.result() is True: success += 1
                p_bar.progress((i + 1) / len(job['r']))
        
        st.session_state.is_running = False
        st.session_state.job_task = None
        st.success(f"Task Done! {success} Inboxed.")
        time.sleep(1)
        st.rerun()
            
    else:
        st.write("")
        col_send, col_logout = st.columns([0.8, 0.2])
        with col_send:
            st.markdown('<div class="send-btn">', unsafe_allow_html=True)
            if st.button("Send All"):
                targets = list(dict.fromkeys([x.strip() for x in list_ui.replace(',', '\n').split('\n') if x.strip()]))
                if email_ui and pass_ui and targets:
                    st.session_state.job_task = {'n': name_ui, 'e': email_ui, 'p': pass_ui, 's1': sub1, 's2': sub2, 's3': sub3, 'b1': body1, 'b2': body2, 'b3': body3, 'r': targets}
                    st.session_state.is_running = True
                    st.rerun()
        with col_logout:
            if st.button("Logout"):
                st.session_state.auth = False
                st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)
