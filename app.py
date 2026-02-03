import os
import smtplib
from flask import Flask, render_template_string, request
from email.message import EmailMessage

app = Flask(__name__)

# --- Configuration (Hosting panel se uthayega) ---
EMAIL_ADDRESS = os.environ.get('EMAIL_USER')
EMAIL_PASSWORD = os.environ.get('EMAIL_PASS')

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bulk Emailer</title>
    <style>
        body { font-family: sans-serif; margin: 40px; background: #f4f4f4; }
        .container { max-width: 600px; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        input, textarea, button { width: 100%; margin-bottom: 15px; padding: 10px; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; }
        button { background: #007bff; color: white; border: none; cursor: pointer; font-weight: bold; }
        button:hover { background: #0056b3; }
        .status { padding: 10px; border-radius: 4px; background: #e2f3ff; color: #004085; }
    </style>
</head>
<body>
    <div class="container">
        <h2>🚀 Bulk Email Sender</h2>
        <form method="POST">
            <input type="text" name="subject" placeholder="Email Subject" required>
            <textarea name="recipients" placeholder="Recipient Emails (comma separated)" rows="4" required></textarea>
            <textarea name="body" placeholder="Write your message here..." rows="6" required></textarea>
            <button type="submit">Send Bulk Emails</button>
        </form>
        {% if status %}<div class="status">{{ status }}</div>{% endif %}
    </div>
</body>
</html>
'''

@app.route('/', methods=['GET', 'POST'])
def home():
    status = ""
    if request.method == 'POST':
        subject = request.form['subject']
        body = request.form['body']
        recipients_raw = request.form['recipients'].split(',')
        
        # Checking if credentials are set
        if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
            return render_template_string(HTML_TEMPLATE, status="❌ Error: Email credentials not set in Environment Variables!")

        try:
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
                for email in recipients_raw:
                    email = email.strip()
                    if email:
                        msg = EmailMessage()
                        msg['Subject'] = subject
                        msg['From'] = EMAIL_ADDRESS
                        msg['To'] = email
                        msg.set_content(body)
                        smtp.send_message(msg)
                status = f"✅ Success! Emails sent to {len(recipients_raw)} recipients."
        except Exception as e:
            status = f"❌ Error: {str(e)}"
            
    return render_template_string(HTML_TEMPLATE, status=status)

if __name__ == '__main__':
    # Port dynamically assigned by hosting provider
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
