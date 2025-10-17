import random, smtplib, os
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()
EMAIL_ADDR = os.getenv("SENDER_EMAIL")
EMAIL_PASS = os.getenv("SENDER_PASS")

def generate_otp():
    return f"{random.randint(100000, 999999)}"

def send_otp_email(to_email, otp):
    msg = EmailMessage()
    msg["Subject"] = "Your Door OTP"
    msg["From"] = EMAIL_ADDR
    msg["To"] = to_email
    msg.set_content(f"Your one-time OTP is: {otp}\nIt will expire in 5 minutes.")
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(EMAIL_ADDR, EMAIL_PASS)
        smtp.send_message(msg)
