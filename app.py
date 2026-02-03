import streamlit as st
import smtplib
import time
import random
import concurrent.futures
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr, make_msgid

# --- Page Setup ---
st.set_page_config(page_title="Mail Console", layout="wide")

# --- Custom CSS for Exact Match ---
st.markdown("""
    <style>
    /* Background and Card */
    .stApp { background-color: #f0f2f6; }
    .main-card {
        background-color: white; padding: 40px; border-radius: 20px;
        box-shadow: 0px 10px 40px rgba(0,0,0,0.1);
        max-width: 1000px; margin: 50px auto; border: 1px solid #e0e4e9;
    }
    
    /* Input Fields Styling */
    input, textarea { 
        color: #555 !important; 
        background-color: #ffffff !important; 
        border: 1px solid #dcdcdc !important;
        border-radius: 10px !important;
        padding: 12px !important;
    }
    
    /* Button Styling */
    div.stButton > button {
        width: 100%; height: 55px; font-size: 18px !important; font-weight: 500;
        border-radius: 12px; border: none; transition: 0.3s;
    }
    .send-btn button { background-color: #4A90E2 !important; color: white !important; }
    .logout-btn button { background-color: #4A90E2 !important; color: white !important; }
    
    /* Hide Header/Footer */
    header {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- Auth Logic ---
if 'auth' not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    col_l, col_m, col_r = st.columns([1, 2, 1])
    with col_m:
        st.write("### Login Required")
        u = st.text_input("User")
        p = st.text_input("Pass", type="password")
        if st.button("Access"):
            if u == "@#2026@#" and p == "@#2026@#":
                st.session_state.auth = True
                st.rerun()
else:
    # --- Main UI ---
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    
    # 6 Columns Layout (Same as Image)
    c1, c2 = st.columns(2)
    with c1: s_name = st.text_input("", placeholder="Sender Name")
    with c2: s_email = st.text_input("", placeholder="Your Gmail")
    
    c3, c4 = st.columns(2)
    with c3: s_pass = st.text_input("", placeholder="App Password", type="password")
    with c4: subject = st.text_input("", placeholder="Email Subject")
    
    c5, c6 = st.columns(2)
    with c5: body = st.text_area("", placeholder="Message Body", height=200)
    with c6: recipients_raw = st.text_area("", placeholder="Recipients (comma / new line)", height=200)

    # --- Secure Sending Engine ---
    def send_task(target):
        try:
            msg = MIMEMultipart()
            msg['Subject'] = subject
            msg['From'] = formataddr((s_name, s_email))
            msg['To'] = target
            msg['Message-ID'] = make_msgid() # Anti-spam unique ID
            msg.attach(MIMEText(body, 'html'))

            with smtplib.SMTP('smtp.gmail.com', 587, timeout=12) as server:
                server.starttls()
                server.login(s_email, s_pass)
                server.send_message(msg)
            
            # Smart Delay to avoid Gmail detection
            time.sleep(random.uniform(0.3, 0.8)) 
            return True
        except Exception as e:
            return str(e)

    # --- Buttons Row ---
    st.write("") # Spacer
    b1, b2 = st.columns(2)
    with b1:
        st.markdown('<div class="send-btn">', unsafe_allow_html=True)
        send_clicked = st.button("Send All")
        st.markdown('</div>', unsafe_allow_html=True)
    with b2:
        st.markdown('<div class="logout-btn">', unsafe_allow_html=True)
        if st.button("Logout"):
            st.session_state.auth = False
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    if send_clicked:
        email_list = list(dict.fromkeys([e.strip() for e in recipients_raw.replace(',', '\n').split('\n') if e.strip()]))
        
        if s_email and s_pass and email_list:
            p_bar = st.progress(0)
            status = st.empty()
            success = 0
            
            # Threading for high speed (max 4 for safety)
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                results = list(executor.map(send_task, email_list))
                
                for i, res in enumerate(results):
                    if res is True: success += 1
                    p_bar.progress((i + 1) / len(email_list))
                    status.text(f"Processing: {i+1}/{len(email_list)}")

            st.success(f"Sent: {success} | Failed: {len(email_list) - success}")
        else:
            st.warning("All fields are required!")

    st.markdown('</div>', unsafe_allow_html=True)
