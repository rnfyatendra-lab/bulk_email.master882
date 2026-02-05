import streamlit as st
import smtplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from concurrent.futures import ThreadPoolExecutor

# --- Page Config ---
st.set_page_config(page_title="Radhe Radhe Fast Mailer", layout="wide")

# --- CSS (Visibility & Design) ---
st.markdown("""
    <style>
    .stApp { background-color: #f0f2f6; }
    .main-card {
        background-color: white; padding: 30px; border-radius: 15px;
        box-shadow: 0px 4px 20px rgba(0,0,0,0.1);
        max-width: 950px; margin: auto; border: 1px solid #e0e4e9;
    }
    input, textarea { color: #000000 !important; font-weight: 500 !important; }
    div.stButton > button:first-child {
        width: 100%; height: 70px; background-color: #FF4B4B !important;
        color: white !important; font-size: 20px !important; font-weight: bold;
        border-radius: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# --- Thread-Safe Email Function ---
def send_fast_email(r_id, job):
    """Har thread apna connection banayega to avoid conflict"""
    try:
        # SMTP setup
        server = smtplib.SMTP('smtp.gmail.com', 587, timeout=10)
        server.starttls()
        server.login(job['e'], job['p'])
        
        # Message creation
        msg = MIMEMultipart()
        msg['From'] = f"{job['n']} <{job['e']}>"
        msg['To'] = r_id
        msg['Subject'] = job['s']
        msg.attach(MIMEText(job['b'], 'plain'))
        
        server.send_message(msg)
        server.quit()
        return True, r_id
    except Exception as e:
        return False, f"{r_id}: {str(e)}"

# --- Session State ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'is_sending' not in st.session_state: st.session_state.is_sending = False

if not st.session_state.logged_in:
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
    if st.button("LOGIN"):
        if u == "RADHE RADHE" and p == "RADHE RADHE":
            st.session_state.logged_in = True
            st.rerun()
else:
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center;'>⚡ Ultra Fast Mailer (Parallel)</h2>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1: s_name = st.text_input("Sender Name", key="sn")
    with col2: s_email = st.text_input("Your Gmail", key="se")
    col3, col4 = st.columns(2)
    with col3: s_pass = st.text_input("App Password", type="password", key="sp")
    with col4: subject = st.text_input("Subject", key="sub")
    col5, col6 = st.columns(2)
    with col5: body = st.text_area("Message Body", height=150, key="msg")
    with col6: recipients_raw = st.text_area("Recipients", height=150, key="rec")

    # --- Fast Sending Engine ---
    if st.session_state.is_sending:
        job = st.session_state.frozen_job
        recipients = job['r']
        
        start_time = time.time()
        status_placeholder = st.empty()
        progress_bar = st.progress(0)
        
        # 'max_workers' ko list size ke hisab se scale kiya gaya hai
        # Gmail usually allows multiple concurrent connections
        workers = min(len(recipients), 25) 
        
        results_ok = 0
        results_err = 0
        
        with ThreadPoolExecutor(max_workers=workers) as executor:
            # Sabhi threads ko ek sath fire karna
            futures = [executor.submit(send_fast_email, r, job) for r in recipients]
            
            for i, future in enumerate(futures):
                success, info = future.result()
                if success: results_ok += 1
                else: results_err += 1
                
                # UI Refresh
                progress_bar.progress((i + 1) / len(recipients))
                status_placeholder.write(f"🚀 Batch Processing... ({results_ok} Success, {results_err} Fail)")

        end_time = time.time()
        st.success(f"✅ Kaam Ho Gaya! {results_ok} Emails sent in {round(end_time - start_time, 2)} seconds.")
        st.session_state.is_sending = False
        st.balloons()
        if st.button("Reset"): st.rerun()

    else:
        if st.button("🔥 FIRE BATCH"):
            emails = list(dict.fromkeys([e.strip() for e in recipients_raw.replace(',', '\n').split('\n') if e.strip()]))
            if s_email and s_pass and emails:
                st.session_state.frozen_job = {
                    'n': s_name, 'e': s_email, 'p': s_pass,
                    's': subject, 'b': body, 'r': emails
                }
                st.session_state.is_sending = True
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
