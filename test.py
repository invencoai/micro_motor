import serial, time, random, smtplib, os
from pymongo import MongoClient
from email.message import EmailMessage
import tkinter as tk
from tkinter import simpledialog, messagebox
from dotenv import load_dotenv
# -------------------- CONFIG --------------------
MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "arduino"
COLL = "test"
SERIAL_PORT = "COM3"     # :warning: CHANGE to your Arduino port
BAUD = 9600
load_dotenv()
EMAIL_ADDR = os.environ.get("SENDER_EMAIL")
EMAIL_PASS = os.environ.get("SENDER_PASS")
# -------------------- DATABASE --------------------
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
users = db[COLL]
# -------------------- SERIAL --------------------
try:
    ser = serial.Serial(SERIAL_PORT, BAUD, timeout=2)
    time.sleep(2)
    print(":white_check_mark: Connected to Arduino")
except Exception as e:
    print(":x: Serial connection failed:", e)
    exit()
# -------------------- HELPERS --------------------
def send_otp_email(to_email, otp):
    msg = EmailMessage()
    msg['Subject'] = 'Your Door OTP'
    msg['From'] = EMAIL_ADDR
    msg['To'] = to_email
    msg.set_content(f'Your one-time OTP is: {otp}\nIt will expire in 5 minutes.')
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(EMAIL_ADDR, EMAIL_PASS)
        smtp.send_message(msg)
def generate_otp():
    return "{:06d}".format(random.randint(0, 999999))
def start_tap_window():
    """Ask Arduino to detect taps within 5 seconds."""
    ser.reset_input_buffer()
    ser.write(b"START_TAP\n")
    start = time.time()
    tap_count = 0
    while time.time() - start < 7:
        line = ser.readline().decode(errors='ignore').strip()
        if line:
            print(line)
        if line.startswith("TAPS:"):
            try:
                tap_count = int(line.split(":")[1])
                break
            except:
                pass
    return tap_count
def open_gate():
    ser.write(b"OPEN\n")
def close_gate():
    ser.write(b"CLOSE\n")
# -------------------- GUI --------------------
root = tk.Tk()
root.title("Secure Door Access")
root.geometry("400x320")
root.eval('tk::PlaceWindow . center')
tk.Label(root, text="Select Registered Email:", font=("Arial", 12)).pack(pady=10)
emails = [u["email"] for u in users.find({}, {"email": 1, "_id": 0})]
if not emails:
    emails = ["No users found"]
selected_email = tk.StringVar(value=emails[0])
tk.OptionMenu(root, selected_email, *emails).pack(pady=10)
status_label = tk.Label(root, text="", fg="gray", font=("Arial", 10))
status_label.pack(pady=5)
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
        status_label.config(text="Sending OTP...")
        root.update_idletasks()
        send_otp_email(email, otp)
        messagebox.showinfo("OTP Sent", f"OTP sent to {email}. Check your inbox.")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to send OTP: {e}")
        return
    entered = simpledialog.askstring("OTP Verification", "Enter the OTP sent to your email:")
    if not entered:
        return
    doc = users.find_one({"email": email})
    if doc and doc.get("otp") == entered and time.time() < doc.get("otp_expiry", 0):
        messagebox.showinfo("Next Step", "Now tap near the sensor within 5 seconds.")
        tap_count = start_tap_window()
        expected = doc.get("tap_code", 2)  # default expected taps = 2
        if tap_count == expected:
            open_gate()
            messagebox.showinfo("Access Granted", ":white_check_mark: Gate opened successfully!")
            root.after(5000, close_gate)
        else:
            messagebox.showerror("Access Denied", f"Taps detected: {tap_count}. Expected: {expected}")
    else:
        messagebox.showerror("Error", "OTP invalid or expired.")
tk.Button(root, text="Request Access", command=request_access, width=25, height=3,
          bg="#4CAF50", fg="white").pack(pady=30)
root.mainloop()