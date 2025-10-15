import serial, time, random, smtplib, os
from pymongo import MongoClient
from email.message import EmailMessage
import tkinter as tk
from tkinter import simpledialog, messagebox
from dotenv import load_dotenv

MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "arduino"
COLL = "test"

SERIAL_PORT = "COM3"     
BAUD = 9600
load_dotenv()  

EMAIL_ADDR = os.environ.get("SENDER_EMAIL")
EMAIL_PASS = os.environ.get("SENDER_PASS")
#  Setup 
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
users = db[COLL]

ser = serial.Serial(SERIAL_PORT, BAUD, timeout=1)
time.sleep(2)

#  Helpers
def send_otp_email(to_email, otp):
    msg = EmailMessage()
    msg['Subject'] = 'Your Door OTP'
    msg['From'] = EMAIL_ADDR
    msg['To'] = to_email
    msg.set_content(f'Your one-time OTP is: {otp}')
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(EMAIL_ADDR, EMAIL_PASS)
        smtp.send_message(msg)

def generate_otp():
    return "{:06d}".format(random.randint(0, 999999))

def start_tap_window():
    ser.write(b"START_TAP\n")
    start = time.time()
    while time.time() - start < 7:
        line = ser.readline().decode().strip()
        if line.startswith("TAPS:"):
            try:
                return int(line.split(":")[1])
            except:
                return 0
    return 0

def open_gate():
    ser.write(b"OPEN\n")

def close_gate():
    ser.write(b"CLOSE\n")

#  GUI 
root = tk.Tk()
root.title("Secure Gate Access System")
root.geometry("400x300")

tk.Label(root, text="Select Your Registered Email:", font=("Arial", 12)).pack(pady=10)

# Fetch emails from MongoDB
emails = [u["email"] for u in users.find({}, {"email": 1, "_id": 0})]
if not emails:
    emails = ["No users found"]

selected_email = tk.StringVar(value=emails[0])
email_dropdown = tk.OptionMenu(root, selected_email, *emails)
email_dropdown.pack(pady=10)

def request_access():
    email = selected_email.get()
    if email == "No users found":
        messagebox.showerror("Error", "No registered users in database.")
        return

    user = users.find_one({"email": email})
    if not user:
        messagebox.showerror("Error", "Email not registered.")
        return

    otp = generate_otp()
    expiry = time.time() + 300  # 5 minutes
    users.update_one({"email": email}, {"$set": {"otp": otp, "otp_expiry": expiry}})
    
    try:
        send_otp_email(email, otp)
        messagebox.showinfo("OTP Sent", f"OTP sent to {email}. Please check your inbox.")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to send OTP: {e}")
        return

    entered = simpledialog.askstring("OTP Verification", "Enter the OTP sent to your email:")
    if not entered:
        return

    doc = users.find_one({"email": email})
    if doc and doc.get("otp") == entered and time.time() < doc.get("otp_expiry", 0):
        messagebox.showinfo("Now Tap", "Please tap near the sensor within 5 seconds.")
        tap_count = start_tap_window()

        expected = doc.get("tap_code", 1)
        if tap_count == expected:
            open_gate()
            messagebox.showinfo("Access Granted", "✅ Gate opened successfully!")
            root.after(5000, close_gate)
        else:
            messagebox.showerror("Access Denied", f"Taps detected: {tap_count}. Expected: {expected}")
    else:
        messagebox.showerror("Error", "OTP invalid or expired.")

btn = tk.Button(root, text="Request Access", command=request_access, width=25, height=3, bg="#4CAF50", fg="white")
btn.pack(pady=30)

root.mainloop()
