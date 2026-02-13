import streamlit as st
import asyncio
import aiosmtplib
from email.message import EmailMessage
from email.utils import formataddr, make_msgid
import time
import random
import uuid

# --- Page Config (Screenshot Match) ---
st.set_page_config(page_title="Secure Mail Console", layout="wide")

# --- UI Styling ---
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    .main-card {
        background-color: white; padding: 40px; border-radius: 20px;
        box-shadow: 0px 10px 40px rgba(0,0,0,0.05);
        max-width: 1100px; margin: auto; border: 1px solid #f0f0f0;
    }
    input, textarea { border-radius: 10px !important; }
    div.stButton > button {
        width: 100%; height: 60px; background-color: #3b82f6 !important;
        color: white !important; font-size: 18px !important; font-weight: 500;
        border-radius: 12px; border: none;
    }
    header, footer {visibility: hidden;}
    [data-testid="stHeader"] {display: none;}
    </style>
""", unsafe_allow_html=True)

# --- Configuration & Limits ---
HOURLY_LIMIT = 28
PARALLEL = 3
DELAY_SEC = 0.12  # 120ms delay

if 'stats' not in st.session_state:
    st.session_state.stats = {} # { 'email': {'count': 0, 'last_reset': time.time()} }

# --- Helper: Reset Hourly Limit ---
def check_limit(email):
    now = time.time()
    if email not in st.session_state.stats:
        st.session_state.stats[email] = {'count': 0, 'last_reset': now}
    
    # 1 ghante baad reset
    if now - st.session_state.stats[email]['last_reset'] > 3600:
        st.session_state.stats[email] = {'count': 0, 'last_reset': now}
    
    return st.session_state.stats[email]['count']

# --- The Async Inbox Engine ---
async def send_mail_task(semaphore, recipient, job):
    async with semaphore:
        try:
            msg = EmailMessage()
            msg["Subject"] = job['s']
            msg["From"] = formataddr((job['n'], job['e']))
            msg["To"] = recipient
            msg["Message-ID"] = make_msgid(domain='gmail.com')
            
            # Inbox Booster Headers (Same as server.js logic)
            msg["X-Mailer"] = "Microsoft Outlook 16.0"
            msg["X-Priority"] = "3"
            msg["X-Entity-Ref-ID"] = uuid.uuid4().hex
            
            # Message Body (No change in text)
            msg.set_content(job['b'])

            await aiosmtplib.send(
                msg,
                hostname="smtp.gmail.com",
                port=587,
                username=job['e'],
                password=job['p'],
                use_tls=False,
                start_tls=True,
                timeout=15
            )
            await asyncio.sleep(DELAY_SEC)
            return True
        except Exception as e:
            return False

async def run_batch(job):
    semaphore = asyncio.BoundedSemaphore(PARALLEL)
    tasks = [send_mail_task(semaphore, r, job) for r in job['targets']]
    results = await asyncio.gather(*tasks)
    return sum(results)

# --- Authentication ---
if 'auth' not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    _, col, _ = st.columns([1, 1, 1])
    with col:
        st.write("### 🔐 Login")
        u = st.text_input("User")
        p = st.text_input("Pass", type="password")
        if st.button("ENTER"):
            if u == "@#2026" and p == "@#2026":
                st.session_state.auth = True
                st.rerun()
else:
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center;'>📧 Secure Mail Launcher</h2>", unsafe_allow_html=True)
    
    # Row 1: 4 Inputs
    c1, c2 = st.columns(2)
    with c1: s_name = st.text_input("Sender Name")
    with c2: s_email = st.text_input("Your Gmail")
    
    c3, c4 = st.columns(2)
    with c3: s_pass = st.text_input("App Password", type="password")
    with c4: subject = st.text_input("Email Subject")
    
    # Row 2: 2 Large Boxes
    c5, c6 = st.columns(2)
    with c5: body = st.text_area("Message Body", height=230)
    with c6: recipients_raw = st.text_area("Recipients", height=230)

    # Action Buttons
    st.write("")
    btn_send, btn_logout = st.columns(2)
    
    with btn_send:
        if st.button("Send All"):
            if s_email and s_pass:
                current_count = check_limit(s_email)
                targets = [x.strip() for x in recipients_raw.replace(',', '\n').split('\n') if x.strip()]
                
                if current_count + len(targets) > HOURLY_LIMIT:
                    st.error(f"Limit Full! You can only send {HOURLY_LIMIT - current_count} more this hour.")
                else:
                    job = {'n': s_name, 'e': s_email, 'p': s_pass, 's': subject, 'b': body, 'targets': targets}
                    with st.spinner("Sending Parallel Batch..."):
                        sent_ok = asyncio.run(run_batch(job))
                        st.session_state.stats[s_email]['count'] += sent_ok
                        st.success(f"Task Completed: {sent_ok} delivered to Inbox!")
    
    with btn_logout:
        if st.button("Logout"):
            st.session_state.auth = False
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)
