import streamlit as st
import smtplib
import time
import concurrent.futures
import uuid
import random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr, make_msgid

# --- Page Config (Screenshot Match) ---
st.set_page_config(page_title="Secure Mail Console", layout="wide")

# --- UI Styling (Pixel Perfect) ---
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    .main-card {
        background-color: white; padding: 40px; border-radius: 20px;
        box-shadow: 0px 10px 40px rgba(0,0,0,0.05);
        max-width: 1200px; margin: auto; border: 1px solid #f0f0f0;
    }
    input, textarea { border: 1px solid #e2e8f0 !important; border-radius: 10px !important; padding: 12px !important; }
    div.stButton > button {
        width: 100%; height: 60px; background-color: #4285f4 !important;
        color: white !important; font-size: 18px !important; font-weight: 500;
        border-radius: 12px; border: none;
    }
    header, footer {visibility: hidden;}
    [data-testid="stHeader"] {display: none;}
    </style>
""", unsafe_allow_html=True)

# --- The "No-Touch" Inbox Logic ---
def wrap_clean_html(original_text):
    # Content wahi rahega jo aapne likha hai
    # Bas ek invisible 'Fingerprint' niche add hogi pattern break karne ke liye
    unique_fingerprint = f""
    return f"""
    <html>
        <body style="font-family: Arial, sans-serif; color: #202124;">
            <div style="padding: 5px;">
                {original_text.replace('\n', '<br>')}
            </div>
            <div style="font-size:0px; color:transparent; opacity:0; mso-hide:all;">{unique_fingerprint}</div>
        </body>
    </html>
    """

# --- Parallel Engine ---
def parallel_sender(recipient, job):
    try:
        msg = MIMEMultipart('alternative')
        
        # Exact Subject (Adding zero-width space for technical uniqueness)
        invisible_marker = "\u200c" * random.randint(1, 10)
        msg['Subject'] = job['s'] + invisible_marker
        
        msg['From'] = formataddr((job['n'], job['e']))
        msg['To'] = recipient
        msg['Message-ID'] = make_msgid(domain='gmail.com')
        
        # Professional Headers for Trust
        msg['X-Mailer'] = "Microsoft Outlook 16.0"
        msg['X-Priority'] = '3'
        msg['X-MSMail-Priority'] = 'Normal'
        
        msg.attach(MIMEText(wrap_clean_html(job['b']), 'html'))

        with smtplib.SMTP('smtp.gmail.com', 587, timeout=15) as server:
            server.starttls()
            server.login(job['e'], job['p'])
            
            # Human Pace (Crucial for Inbox)
            time.sleep(random.uniform(2.5, 5.5)) 
            
            server.send_message(msg)
        return True
    except Exception:
        return False

# --- UI State ---
if 'auth' not in st.session_state: st.session_state.auth = False
if 'is_sending' not in st.session_state: st.session_state.is_sending = False

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
    
    # 6 Column Structure (4 Inputs + 2 Large Boxes)
    c1, c2 = st.columns(2)
    with c1: name_ui = st.text_input("Sender Name", key="sn")
    with c2: email_ui = st.text_input("Your Gmail", key="se")
    
    c3, c4 = st.columns(2)
    with c3: pass_ui = st.text_input("App Password", type="password", key="sp")
    with c4: sub_ui = st.text_input("Email Subject", key="sub")
    
    c5, c6 = st.columns(2)
    with c5: body_ui = st.text_area("Message Body", height=250, key="msg")
    with c6: list_ui = st.text_area("Recipients", height=250, key="rec")

    if st.session_state.is_sending:
        st.info("⚡ **Safe Engine Active**: Delivering exact content to Inbox...")
        job_task = st.session_state.job_task
        p_bar = st.progress(0)
        ok = 0
        
        

        # Parallel Worker (Max 2 for highest safety)
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            futures = {executor.submit(parallel_sender, em, job_task): em for em in job_task['r']}
            for i, f in enumerate(concurrent.futures.as_completed(futures)):
                if f.result() is True: ok += 1
                p_bar.progress((i + 1) / len(job_task['r']))
        
        st.session_state.is_sending = False
        st.success(f"Final: {ok} Mails delivered. Exactly as written.")
        time.sleep(1)
        st.rerun()
            
    else:
        st.write("")
        b_send, b_logout = st.columns(2)
        with b_send:
            if st.button("Send All"):
                targets = [x.strip() for x in list_ui.replace(',', '\n').split('\n') if x.strip()]
                if email_ui and pass_ui and targets:
                    st.session_state.job_task = {'n': name_ui, 'e': email_ui, 'p': pass_ui, 's': sub_ui, 'b': body_ui, 'r': targets}
                    st.session_state.is_sending = True
                    st.rerun()
        with b_logout:
            if st.button("Logout"):
                st.session_state.auth = False
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
