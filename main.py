import tkinter as tk
from tkinter import messagebox
from db import get_all_emails, get_user, set_otp, verify_otp
from email_utils import generate_otp, send_otp_email
from arduino_control import start_tap_window, open_gate, close_gate

#  GUI SETUP 
root = tk.Tk()
root.title("🔒 Secure Door Access System")
root.geometry("420x400")
root.resizable(False, False)
root.eval("tk::PlaceWindow . center")

tk.Label(root, text="Select Registered Email:", font=("Arial", 12, "bold")).pack(pady=15)

emails = get_all_emails()
if not emails:
    emails = ["No users found"]

selected_email = tk.StringVar(value=emails[0])
tk.OptionMenu(root, selected_email, *emails).pack(pady=10)

status_label = tk.Label(root, text="", fg="gray", font=("Arial", 11))
status_label.pack(pady=10)
entry_label = tk.Label(root, text="", font=("Arial", 11))
entry_label.pack()

otp_entry = tk.Entry(root, font=("Arial", 12), justify="center")
otp_entry.pack_forget()
submit_btn = None

#  HELPER 
def show_status(text, color="black"):
    status_label.config(text=text, fg=color)
    root.update_idletasks()

#  LOGIC 
def request_access():
    email = selected_email.get()
    if email == "No users found":
        show_status("⚠️ No registered users found.", "red")
        return

    user = get_user(email)
    if not user:
        show_status("❌ Email not registered.", "red")
        return

    otp = generate_otp()
    set_otp(email, otp)

    try:
        show_status("📤 Sending OTP...")
        send_otp_email(email, otp)
        show_status(f"✅ OTP sent to {email}")
        entry_label.config(text="Enter the OTP below:")
        otp_entry.delete(0, tk.END)
        otp_entry.pack(pady=10)
        global submit_btn
        if not submit_btn:
            submit_btn = tk.Button(root, text="Verify OTP", command=lambda: verify_otp_handler(email),
                                   bg="#0078D7", fg="white", width=20, height=2)
            submit_btn.pack(pady=20)
    except Exception as e:
        show_status(f"❌ Failed to send OTP: {e}", "red")

def verify_otp_handler(email):
    entered_otp = otp_entry.get().strip()
    if not entered_otp:
        show_status("⚠️ Please enter OTP.", "red")
        return

    if verify_otp(email, entered_otp):
        show_status("✅ OTP Verified! Tap near the sensor...", "green")
        otp_entry.pack_forget()
        entry_label.config(text="")
        root.after(1000, lambda: tap_access(email))
    else:
        show_status("❌ OTP invalid or expired.", "red")

def tap_access(email):
    user = get_user(email)
    tap_count = start_tap_window()
    expected = user.get("tap_code", 2)

    if tap_count == expected:
        show_status("✅ Access Granted. Gate Opening...", "green")
        open_gate()
        root.after(5000, close_gate)
        root.after(5000, lambda: show_status("🔒 Gate Closed. Ready for next user.", "gray"))
    else:
        show_status("❌ Access Denied. Wrong tap pattern.", "red")

#  BUTTON 
tk.Button(root, text="Request Access", command=request_access,
          width=25, height=3, bg="#4CAF50", fg="white").pack(pady=30)

root.mainloop()
