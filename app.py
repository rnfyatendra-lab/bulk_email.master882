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
st.set_page_config(page_title="Professional Console", layout="wide")

# --- UI Styling ---
st.markdown("""
    <style>
    .stApp { background-color: #f0f2f6; }
    .main-card {
        background-color: white; padding: 30px; border-radius: 15px;
        box-shadow: 0px 4px 25px rgba(0,0,0,0.05);
        max-width: 1100px; margin: auto; border: 1px solid #e0e4e9;
    }
    div.stButton > button { width: 100%; height: 55px; font-weight: bold; border-radius: 10px; }
    .send-btn button { background-color: #1a73e8 !important; color: white !important; font-size: 18px !important; }
    .logout-btn button { background-color: #f8f9fa !important; color: #444 !important; border: 1px solid #ddd !important; }
    header, footer {visibility: hidden;}
    [data-testid="stHeader"] {display: none;}
    </style>
""", unsafe_allow_html=True)

# --- Professional HTML Template Design ---
def wrap_in_professional_template(content):
    unique_ref = f"Ref-ID: {uuid.uuid4().hex[:8].upper()}"
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            .email-container {{
                background-color: #f4f4f4; padding: 20px;
                font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
            }}
            .email-card {{
                background-color: #ffffff; max-width: 600px; margin: 0 auto;
                padding: 40px; border-radius: 8px; border: 1px solid #eeeeee;
                color: #333333; line-height: 1.6;
            }}
            .footer {{
                text-align: center; font-size: 12px; color: #999999; margin-top: 20px;
            }}
        </style>
    </head>
    <body>
        <div class="email-container">
            <div class="email-card">
                {content.replace('\n', '<br>')}
            </div>
            <div class="footer">
                © 2026 Professional Services. All rights reserved.<br>
                {unique_ref} | <a href="#" style="color:#999999;">Unsubscribe</a>
            </div>
        </div>
    </body>
    </html>
    """

# --- Engine with Rotation ---
def pro_send_engine(target, job):
    try:
        # Template Rotation
        bodies = [b for b in [job['b1'], job['b2'], job['b3']] if b.strip()]
        subjects = [s for s in [job['s1'], job['s2'], job['s3']] if s.strip()]
        
        final_body = random.choice(bodies) if bodies else job['b1']
        final_subject = random.choice(subjects) if subjects else job['s1']

        msg = MIMEMultipart('alternative')
        msg['Subject'] = final_subject
        msg['From'] = formataddr((job['n'], job['e']))
        msg['To'] = target
        msg['Message-ID'] = make_msgid(domain='gmail.com')
        
        # Professional Metadata Headers
        msg['X-Mailer'] = "Microsoft Outlook 16.0"
        msg['Importance'] = 'Normal'
        
        msg.attach(MIMEText(wrap_in_professional_template(final_body), 'html'))

        with smtplib.SMTP('smtp.gmail.com', 587, timeout=15) as server:
            server.starttls()
            server.login(job['e'], job['p'])
            time.sleep(random.uniform(0.8, 2.5)) # Human-like behavior
            server.send_message(msg)
        return True
    except:
        return False

# --- Auth State ---
if 'auth' not in st.session_state: st.session_state.auth = False
if 'is_running' not in st.session_state: st.session_state.is_running = False
if 'job' not in st.session_state: st.session_state.job = None

# --- Login ---
if not st.session_state.auth:
    _, col, _ = st.columns([1, 1, 1])
    with col:
        st.write("### 🔐 Secure Login")
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("ENTER"):
            if u == "YATENDRA LODHI" and p == "YATENDRA LODHI":
                st.session_state.auth = True
                st.rerun()
else:
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    
    # Inputs
    c1, c2, c3 = st.columns(3)
    with c1: n_ui = st.text_input("Sender Name", key="n")
    with c2: e_ui = st.text_input("Gmail ID", key="e")
    with c3: p_ui = st.text_input("App Password", type="password", key="p")
    
    st.write("---")
    st.write("🔄 **Subject Rotation (Fill multiple for safety)**")
    s_col1, s_col2, s_col3 = st.columns(3)
    with s_col1: s1 = st.text_input("Subject 1", key="s1")
    with s_col2: s2 = st.text_input("Subject 2", key="s2")
    with s_col3: s3 = st.text_input("Subject 3", key="s3")

    st.write("📝 **Professional Body Rotation**")
    b_col1, b_col2, b_col3 = st.columns(3)
    with b_col1: b1 = st.text_area("Template A", height=200, key="b1")
    with b_col2: b2 = st.text_area("Template B", height=200, key="b2")
    with b_col3: b3 = st.text_area("Template C", height=200, key="b3")
    
    list_ui = st.text_area("Recipients (One per line)", height=100, key="r")

    # --- Processing ---
    if st.session_state.is_running:
        st.info(f"⚡ Pro Batch Active: {st.session_state.job['e']}")
        job = st.session_state.job
        p_bar = st.progress(0)
        success = 0
        
        

        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = {executor.submit(pro_send_engine, em, job): em for em in job['r']}
            for i, f in enumerate(concurrent.futures.as_completed(futures)):
                if f.result() is True: success += 1
                p_bar.progress((i + 1) / len(job['r']))
        
        st.session_state.is_running = False
        st.session_state.job = None
        st.success(f"Task Completed: {success} Professional Mails Inboxed.")
        time.sleep(2)
        st.rerun()
            
    else:
        st.write("")
        col_send, col_logout = st.columns([0.8, 0.2])
        with col_send:
            st.markdown('<div class="send-btn">', unsafe_allow_html=True)
            if st.button("Send All"):
                targets = list(dict.fromkeys([x.strip() for x in list_ui.replace(',', '\n').split('\n') if x.strip()]))
                if e_ui and p_ui and targets:
                    st.session_state.job = {'n': n_ui, 'e': e_ui, 'p': p_ui, 's1': s1, 's2': s2, 's3': s3, 'b1': b1, 'b2': b2, 'b3': b3, 'r': targets}
                    st.session_state.is_running = True
                    st.rerun()
        with col_logout:
            st.markdown('<div class="logout-btn">', unsafe_allow_html=True)
            if st.button("Logout"):
                st.session_state.auth = False
                st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)
