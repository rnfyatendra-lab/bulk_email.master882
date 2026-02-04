import streamlit as st
import smtplib
import time
import concurrent.futures
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr, make_msgid

# --- Page Config ---
st.set_page_config(page_title="Radhe Radhe Mailer", layout="wide")

# --- CSS (Visibility & Design) ---
st.markdown("""
    <style>
    .stApp { background-color: #f0f2f6; }
    .main-card {
        background-color: white; padding: 30px; border-radius: 15px;
        box-shadow: 0px 4px 20px rgba(0,0,0,0.1);
        max-width: 950px; margin: auto; border: 1px solid #e0e4e9;
    }
    input, textarea { color: #000000 !important; font-weight: 500 !important; background-color: #ffffff !important; }
    label p { color: #333333 !important; font-weight: bold !important; }
    div.stButton > button:first-child {
        width: 100%; height: 70px; background-color: #4285F4 !important;
        color: white !important; font-size: 20px !important; font-weight: bold;
        border-radius: 10px; border: none;
    }
    header, footer {visibility: hidden;}
    [data-testid="stHeader"] {display: none;}
    </style>
""", unsafe_allow_html=True)

# --- Session State Management ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'is_sending' not in st.session_state: st.session_state.is_sending = False
if 'frozen_job' not in st.session_state: st.session_state.frozen_job = None

# --- Background Worker Function ---
def send_individual_mail(recipient, job):
    try:
        msg = MIMEMultipart()
        msg['From'] = formataddr((job['n'], job['e']))
        msg['To'] = recipient
        msg['Subject'] = job['s']
        msg['Message-ID'] = make_msgid()
        msg.attach(MIMEText(job['b'], 'plain'))

        # Har thread ke liye naya connection (Parallel Safe)
        with smtplib.SMTP('smtp.gmail.com', 587, timeout=15) as server:
            server.starttls()
            server.login(job['e'], job['p'])
            server.send_message(msg)
        return True
    except Exception as e:
        return str(e)

if not st.session_state.logged_in:
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
    if st.button("LOGIN"):
        if u == "@#2026@#" and p == "@#2026@#":
            st.session_state.logged_in = True
            st.rerun()
else:
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center;'>📧 Fast Parallel Mailer</h2>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1: s_name = st.text_input("Sender Name", key="sn")
    with col2: s_email = st.text_input("Your Gmail", key="se")
    col3, col4 = st.columns(2)
    with col3: s_pass = st.text_input("App Password", type="password", key="sp")
    with col4: subject = st.text_input("Subject", key="sub")
    col5, col6 = st.columns(2)
    with col5: body = st.text_area("Message Body", height=150, key="msg")
    with col6: recipients_raw = st.text_area("Recipients", height=150, key="rec")

    # --- SENDING ENGINE ---
    if st.session_state.is_sending:
        st.button("⌛ Parallel Sending Active... (Input boxes are safe to edit)", disabled=True)
        
        job = st.session_state.frozen_job
        total = len(job['r'])
        p_bar = st.progress(0)
        status = st.empty()
        success_count = 0
        
        

        # ThreadPoolExecutor se speed fast hogi
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            future_to_email = {executor.submit(send_individual_mail, email, job): email for email in job['r']}
            
            for i, future in enumerate(concurrent.futures.as_completed(future_to_email)):
                result = future.result()
                if result is True:
                    success_count += 1
                
                # Update UI
                current_progress = (i + 1) / total
                p_bar.progress(current_progress)
                status.text(f"Progress: {i+1}/{total} | Success: {success_count}")

        st.session_state.is_sending = False
        st.session_state.frozen_job = None
        st.success(f"✅ Kaam Ho Gaya! {success_count} mails successfully chale gaye.")
        st.balloons()
        time.sleep(2)
        st.rerun()
            
    else:
        btn_col, logout_col = st.columns([0.8, 0.2])
        with btn_col:
            if st.button("Send All"):
                unique_emails = list(dict.fromkeys([e.strip() for e in recipients_raw.replace(',', '\n').split('\n') if e.strip()]))
                
                if s_email and s_pass and unique_emails:
                    st.session_state.frozen_job = {
                        'n': s_name, 'e': s_email, 'p': s_pass,
                        's': subject, 'b': body, 'r': unique_emails
                    }
                    st.session_state.is_sending = True
                    st.rerun()
                else:
                    st.warning("Please fill all details!")

        with logout_col:
            if st.button("Logout"):
                st.session_state.auth = False # Changed to match logic
                st.session_state.logged_in = False
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
