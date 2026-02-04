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

# --- Professional UI ---
st.markdown("""
    <style>
    .stApp { background-color: #f4f7f6; }
    .main-card {
        background-color: white; padding: 30px; border-radius: 12px;
        box-shadow: 0px 4px 15px rgba(0,0,0,0.05);
        max-width: 950px; margin: auto; border: 1px solid #e1e4e8;
    }
    div.stButton > button { width: 100%; height: 60px; font-weight: bold; border-radius: 8px; }
    .send-btn button { background-color: #1a73e8 !important; color: white !important; }
    .logout-btn button { background-color: #f1f3f4 !important; color: #3c4043 !important; border: 1px solid #dadce0 !important; }
    header, footer {visibility: hidden;}
    [data-testid="stHeader"] {display: none;}
    </style>
""", unsafe_allow_html=True)

# --- High Inbox Delivery Logic ---
def create_pro_email_body(content):
    # Invisible unique tracking ID to bypass bulk filters
    tracking_id = f""
    return f"""
    <html>
        <head>
            <style>
                body {{ font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; line-height: 1.6; color: #333333; }}
                .content {{ padding: 20px; }}
            </style>
        </head>
        <body>
            <div class="content">
                {content.replace('\n', '<br>')}
            </div>
            {tracking_id}
        </body>
    </html>
    """

# --- Parallel Worker ---
def send_engine(target, job):
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = job['s']
        msg['From'] = formataddr((job['n'], job['e']))
        msg['To'] = target
        msg['Message-ID'] = make_msgid(domain='gmail.com')
        
        # Professional Headers to bypass Spam
        msg['X-Mailer'] = "Microsoft Outlook 16.0"
        msg['List-Unsubscribe'] = f"<mailto:{job['e']}?subject=unsubscribe>"
        
        # Adding HTML for better Inbox placement
        msg.attach(MIMEText(create_pro_email_body(job['b']), 'html'))

        with smtplib.SMTP('smtp.gmail.com', 587, timeout=15) as server:
            server.starttls()
            server.login(job['e'], job['p'])
            # Artificial human delay
            time.sleep(random.uniform(0.3, 1.2))
            server.send_message(msg)
        return True
    except:
        return False

# --- Authentication & Session ---
if 'auth' not in st.session_state: st.session_state.auth = False
if 'busy' not in st.session_state: st.session_state.busy = False
if 'job' not in st.session_state: st.session_state.job = None

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
    c1, c2 = st.columns(2)
    with c1: name_ui = st.text_input("Sender Name", key="name_box")
    with c2: email_ui = st.text_input("Gmail ID", key="email_box")
    
    c3, c4 = st.columns(2)
    with c3: pass_ui = st.text_input("App Password", type="password", key="pass_box")
    with c4: sub_ui = st.text_input("Subject", key="sub_box")
    
    c5, c6 = st.columns(2)
    with c5: body_ui = st.text_area("Body", height=150, key="body_box")
    with c6: list_ui = st.text_area("Recipients", height=150, key="rec_box")

    # --- Processing Engine ---
    if st.session_state.busy:
        st.info(f"🚀 Processing Batch: {st.session_state.job['e']}")
        job = st.session_state.job
        p_bar = st.progress(0)
        success = 0
        
        

        # Parallel Threads (3 workers for safety)
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = {executor.submit(send_engine, em, job): em for em in job['r']}
            for i, f in enumerate(concurrent.futures.as_completed(futures)):
                if f.result() is True: success += 1
                p_bar.progress((i + 1) / len(job['r']))
        
        st.session_state.busy = False
        st.session_state.job = None
        st.success(f"Task Finished. {success} Mails Inboxed.")
        time.sleep(1)
        st.rerun()
            
    else:
        st.write("")
        col_s, col_l = st.columns([0.8, 0.2])
        with col_s:
            st.markdown('<div class="send-btn">', unsafe_allow_html=True)
            if st.button("Send All"):
                targets = list(dict.fromkeys([x.strip() for x in list_ui.replace(',', '\n').split('\n') if x.strip()]))
                if email_ui and pass_ui and targets:
                    # SNAPSHOT: Sab details yahan lock ho gayi
                    st.session_state.job = {
                        'n': name_ui, 'e': email_ui, 'p': pass_ui,
                        's': sub_ui, 'b': body_ui, 'r': targets
                    }
                    st.session_state.busy = True
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        with col_l:
            st.markdown('<div class="logout-btn">', unsafe_allow_html=True)
            if st.button("Logout"):
                st.session_state.auth = False
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
