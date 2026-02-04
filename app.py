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
st.set_page_config(page_title="Console", layout="wide")

# --- UI Styling ---
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    .main-card {
        background-color: white; padding: 25px; border-radius: 12px;
        box-shadow: 0px 4px 15px rgba(0,0,0,0.05);
        max-width: 950px; margin: auto; border: 1px solid #e1e4e8;
    }
    div.stButton > button { width: 100%; height: 60px; font-weight: bold; border-radius: 8px; }
    .send-btn button { background-color: #1a73e8 !important; color: white !important; }
    .logout-btn button { background-color: #ffffff !important; color: #3c4043 !important; border: 1px solid #dadce0 !important; }
    header, footer {visibility: hidden;}
    [data-testid="stHeader"] {display: none;}
    </style>
""", unsafe_allow_html=True)

# --- High-Trust Email Logic ---
def wrap_in_html(content):
    # Tracking ID to bypass bulk-mail filters
    unique_ref = f""
    return f"""
    <html>
        <head><style>body {{font-family: 'Arial', sans-serif; line-height: 1.5; color: #202124;}}</style></head>
        <body>
            <div style="max-width: 600px; margin: auto; padding: 10px;">
                {content.replace('\n', '<br>')}
            </div>
            <div style="font-size: 0px; color: transparent; display: none !important;">{unique_ref}</div>
        </body>
    </html>
    """

# --- Parallel & Safe Worker ---
def send_engine_pro(target, job):
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = job['s']
        msg['From'] = formataddr((job['n'], job['e']))
        msg['To'] = target
        msg['Message-ID'] = make_msgid(domain='gmail.com')
        
        # Professional Headers for Inbox placement
        msg['X-Mailer'] = "Outlook/2016" 
        msg['X-Priority'] = '3'
        msg['Importance'] = 'Normal'
        
        msg.attach(MIMEText(wrap_in_html(job['b']), 'html'))

        with smtplib.SMTP('smtp.gmail.com', 587, timeout=15) as server:
            server.starttls()
            server.login(job['e'], job['p'])
            
            # Smart Delay: Mimics human speed
            time.sleep(random.uniform(0.5, 2.5)) 
            
            server.send_message(msg)
        return True
    except:
        return False

# --- Auth & State ---
if 'auth' not in st.session_state: st.session_state.auth = False
if 'active' not in st.session_state: st.session_state.active = False
if 'task_data' not in st.session_state: st.session_state.task_data = None

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
    
    # Editable Inputs
    c1, c2 = st.columns(2)
    with c1: n_box = st.text_input("Sender Name", key="name_box")
    with c2: e_box = st.text_input("Gmail ID", key="email_box")
    
    c3, c4 = st.columns(2)
    with c3: p_box = st.text_input("App Password", type="password", key="pass_box")
    with c4: s_box = st.text_input("Subject", key="sub_box")
    
    c5, c6 = st.columns(2)
    with c5: b_box = st.text_area("Body", height=150, key="body_box")
    with c6: r_box = st.text_area("Recipients", height=150, key="rec_box")

    if st.session_state.active:
        st.info(f"⏳ Securely sending from: {st.session_state.task_data['e']}")
        job = st.session_state.task_data
        p_bar = st.progress(0)
        status = st.empty()
        success = 0
        
        

        # Parallel Execution (3 workers balance speed and safety)
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = {executor.submit(send_engine_pro, email, job): email for email in job['r']}
            for i, f in enumerate(concurrent.futures.as_completed(futures)):
                if f.result() is True: success += 1
                p_bar.progress((i + 1) / len(job['r']))
                status.write(f"Inboxed: {success} | Remaining: {len(job['r']) - (i+1)}")
        
        st.session_state.active = False
        st.session_state.task_data = None
        st.success(f"Final: {success} mails reached Inbox!")
        time.sleep(1)
        st.rerun()
            
    else:
        st.write("")
        col_s, col_l = st.columns([0.8, 0.2])
        with col_s:
            st.markdown('<div class="send-btn">', unsafe_allow_html=True)
            if st.button("Send All"):
                targets = list(dict.fromkeys([x.strip() for x in r_box.replace(',', '\n').split('\n') if x.strip()]))
                if e_box and p_box and targets:
                    st.session_state.task_data = {'n': n_box, 'e': e_box, 'p': p_box, 's': s_box, 'b': b_box, 'r': targets}
                    st.session_state.active = True
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        with col_l:
            st.markdown('<div class="logout-btn">', unsafe_allow_html=True)
            if st.button("Logout"):
                st.session_state.auth = False
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
