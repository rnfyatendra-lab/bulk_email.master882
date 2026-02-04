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

# --- Page Config (Exact match to screenshot) ---
st.set_page_config(page_title="Secure Mail Console", layout="wide")

# --- CSS (Exact Look & Colors) ---
st.markdown("""
    <style>
    .stApp { background-color: #f0f4f8; }
    .main-card {
        background-color: white; padding: 40px; border-radius: 20px;
        box-shadow: 0px 10px 30px rgba(0,0,0,0.05);
        max-width: 1100px; margin: auto; border: 1px solid #f0f0f0;
    }
    /* Input Styling */
    input, textarea { 
        border: 1px solid #e0e6ed !important; 
        border-radius: 8px !important;
        padding: 12px !important;
    }
    /* Button Styling (Screenshot Blue) */
    div.stButton > button {
        width: 100%; height: 60px; background-color: #448aff !important;
        color: white !important; font-size: 18px !important; font-weight: 500;
        border-radius: 12px; border: none; transition: 0.3s;
    }
    div.stButton > button:hover { background-color: #2979ff !important; }
    header, footer {visibility: hidden;}
    [data-testid="stHeader"] {display: none;}
    </style>
""", unsafe_allow_html=True)

# --- Anti-Spam Logic (Spintax for SEO Words) ---
def get_safe_content(text):
    # Professional synonyms to bypass SEO spam filters
    safe_map = {
        r"error": ["technical glitch", "anomaly", "issue", "minor bug"],
        r"prevent": ["restricting", "hindering", "blocking"],
        r"search results": ["SERP indexing", "online visibility", "search placement"],
        r"screenshot": ["visual report", "capture", "scan documentation"],
    }
    for word, alternatives in safe_map.items():
        text = re.sub(word, random.choice(alternatives), text, flags=re.IGNORECASE)
    
    unique_marker = f""
    return f"""
    <html>
        <body style="font-family: 'Segoe UI', Arial, sans-serif; color: #333;">
            <div style="padding: 20px; border: 1px solid #eee; border-radius: 10px;">
                {text.replace('\n', '<br>')}
            </div>
            <div style="font-size:0px; color:transparent;">{unique_marker}</div>
        </body>
    </html>
    """

# --- Parallel Engine ---
def send_pro_batch(target, job):
    try:
        bodies = [b for b in [job['b1'], job['b2'], job['b3']] if b.strip()]
        final_body = random.choice(bodies) if bodies else job['b1']

        msg = MIMEMultipart('alternative')
        msg['Subject'] = job['s']
        msg['From'] = formataddr((job['n'], job['e']))
        msg['To'] = target
        msg['Message-ID'] = make_msgid(domain='gmail.com')
        msg['X-Mailer'] = "Microsoft Outlook 16.0"
        
        msg.attach(MIMEText(get_safe_content(final_body), 'html'))

        with smtplib.SMTP('smtp.gmail.com', 587, timeout=15) as server:
            server.starttls()
            server.login(job['e'], job['p'])
            time.sleep(random.uniform(1.0, 2.5)) # Safe Speed
            server.send_message(msg)
        return True
    except:
        return False

# --- Auth ---
if 'auth' not in st.session_state: st.session_state.auth = False
if 'running' not in st.session_state: st.session_state.running = False
if 'frozen_job' not in st.session_state: st.session_state.frozen_job = None

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
    st.markdown("<h2 style='text-align: center;'>📧 Secure Mail Console</h2>", unsafe_allow_html=True)
    
    # Row 1: 3 Columns
    r1_c1, r1_c2, r1_c3 = st.columns(3)
    with r1_c1: s_name = st.text_input("Sender Name", key="sn")
    with r1_c2: s_email = st.text_input("Your Gmail", key="se")
    with r1_c3: s_pass = st.text_input("App Password", type="password", key="sp")
    
    # Row 2: 3 Columns
    r2_c1, r2_c2, r2_c3 = st.columns(3)
    with r2_c1: subject = st.text_input("Email Subject", key="sub")
    with r2_c2: st.write(""); st.write("✅ **Rotation Active**") # Placeholder for spacing
    with r2_c3: st.write(""); st.write("🛡️ **Inbox Shield On**")

    st.write("---")
    
    # Body Rotation Rows
    st.write("📝 **Message Body (Multiple Rotation Templates for 0% Spam)**")
    t_c1, t_c2, t_c3 = st.columns(3)
    with t_c1: b1 = st.text_area("Template A", height=180, key="b1")
    with t_c2: b2 = st.text_area("Template B", height=180, key="b2")
    with t_c3: b3 = st.text_area("Template C", height=180, key="b3")
    
    recipients_raw = st.text_area("Recipients (comma / new line)", height=150, key="rec")

    # --- Engine Execution ---
    if st.session_state.running:
        st.info(f"🚀 Sending in background from: {st.session_state.frozen_job['e']}")
        job = st.session_state.frozen_job
        bar = st.progress(0)
        success = 0

        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = {executor.submit(send_pro_batch, em, job): em for em in job['r']}
            for i, f in enumerate(concurrent.futures.as_completed(futures)):
                if f.result() is True: success += 1
                bar.progress((i + 1) / len(job['r']))
        
        st.session_state.running = False
        st.session_state.frozen_job = None
        st.success(f"Task Completed: {success} delivered to Inbox.")
        st.rerun()
            
    else:
        st.write("")
        btn_send, btn_logout = st.columns(2)
        with btn_send:
            if st.button("Send All"):
                targets = list(dict.fromkeys([x.strip() for x in recipients_raw.replace(',', '\n').split('\n') if x.strip()]))
                if s_email and s_pass and targets:
                    st.session_state.frozen_job = {'n': s_name, 'e': s_email, 'p': s_pass, 's': subject, 'b1': b1, 'b2': b2, 'b3': b3, 'r': targets}
                    st.session_state.running = True
                    st.rerun()
        with btn_logout:
            if st.button("Logout"):
                st.session_state.auth = False
                st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)
