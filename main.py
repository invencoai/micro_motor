import tkinter as tk
from PIL import Image, ImageTk
from db import get_all_emails, get_user, set_otp, verify_otp
from email_utils import generate_otp, send_otp_email
from arduino_control import start_tap_window, open_gate, close_gate
import time
import os
from PIL import Image, ImageTk

#  GUI SETUP 

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
logo_path = os.path.join(BASE_DIR, "logo.png")


root = tk.Tk()
root.title("🔒 Secure Door Access System")
root.geometry("500x580")
root.resizable(False, False)
root.configure(bg="#1F1F2E")
root.eval("tk::PlaceWindow . center")

# Fonts
title_font = ("Helvetica", 18, "bold")
company_font = ("Helvetica", 16, "bold")
label_font = ("Helvetica", 12)
button_font = ("Helvetica", 13, "bold")

#  COMPANY LOGO AND NAME 
try:
    logo_image = Image.open(logo_path)
    logo_image = logo_image.resize((50, 50), Image.Resampling.LANCZOS)
    logo_photo = ImageTk.PhotoImage(logo_image)
    logo_label = tk.Label(root, image=logo_photo, bg="#1F1F2E")
    logo_label.image = logo_photo  # keep reference
    logo_label.pack(pady=(10,0))
except Exception as e:
    print("⚠️ Logo not loaded:", e)
    logo_photo = None

tk.Label(root, text="Invenco AI", font=company_font, fg="#FFD700", bg="#1F1F2E").pack(pady=(0,10))

# Header
tk.Label(root, text="🔒 Secure Door Access", font=title_font, fg="#00FFFF", bg="#1F1F2E").pack(pady=10)

# Email selection
tk.Label(root, text="Select Registered Email:", font=label_font, fg="#00FFFF", bg="#1F1F2E").pack(pady=5)

emails = get_all_emails()
if not emails:
    emails = ["No users found"]

selected_email = tk.StringVar(value=emails[0])

option_menu = tk.OptionMenu(root, selected_email, *emails)
option_menu.pack(pady=5)
option_menu.config(bg="#4CAF50", fg="white", font=label_font, width=25)
option_menu["menu"].config(bg="#4CAF50", fg="white", font=label_font)

# Status, OTP, Tap info, Door info
status_label = tk.Label(root, text="", fg="gray", font=label_font, bg="#1F1F2E")
status_label.pack(pady=5)

entry_label = tk.Label(root, text="", font=label_font, bg="#1F1F2E")
entry_label.pack()

otp_entry = tk.Entry(root, font=label_font, justify="center")
otp_entry.pack_forget()

tap_info_label = tk.Label(root, text="", font=label_font, fg="#00FF7F", bg="#1F1F2E")
tap_info_label.pack(pady=5)

door_info_label = tk.Label(root, text="", font=label_font, fg="#FFD700", bg="#1F1F2E")
door_info_label.pack(pady=5)

#  HELPER 
def show_status(text, color="white"):
    status_label.config(text=text, fg=color)
    root.update_idletasks()

def update_tap_info(remaining_time, tap_count):
    tap_info_label.config(text=f"Taps detected: {tap_count} | Time remaining: {remaining_time}s")
    root.update_idletasks()

def update_door_info(remaining_time):
    door_info_label.config(text=f"Door will close in: {remaining_time}s")
    root.update_idletasks()

#  BUTTON LOGIC 
def main_button_handler():
    if main_button["text"] == "Request Access":
        request_access()
    else:
        verify_otp_handler(selected_email.get())

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
        show_status("📤 Sending OTP...", "#00FFFF")
        send_otp_email(email, otp)
        show_status(f"✅ OTP sent to {email}", "#00FF7F")
        entry_label.config(text="Enter the OTP below:")
        otp_entry.delete(0, tk.END)
        otp_entry.pack(pady=10)
        main_button.config(text="Verify OTP")
    except Exception as e:
        show_status(f"❌ Failed to send OTP: {e}", "red")

def verify_otp_handler(email):
    entered_otp = otp_entry.get().strip()
    if not entered_otp:
        show_status("⚠️ Please enter OTP.", "red")
        return

    if verify_otp(email, entered_otp):
        show_status("✅ OTP Verified! Tap near the sensor...", "#00FF7F")
        otp_entry.pack_forget()
        entry_label.config(text="")
        main_button.config(text="Request Access")
        root.after(500, lambda: tap_access(email))
    else:
        show_status("❌ OTP invalid or expired.", "red")

#  TAP AND DOOR 
def tap_access(email):
    user = get_user(email)
    expected_taps = user.get("tap_code", 2)
    duration = 10
    final_tap_count = 0  # store the last non-zero tap count

    start_time = time.time()
    show_status("⏳ Tap near the sensor now...", "#00FFFF")

    while time.time() - start_time < duration:
        tap_count = start_tap_window()  # Arduino returns current taps
        if tap_count > 0:
            final_tap_count = tap_count  # store last valid tap count
        remaining = duration - int(time.time() - start_time)
        update_tap_info(remaining, final_tap_count)
        root.update()
        time.sleep(0.1)

    tap_info_label.config(text="")

    if final_tap_count == expected_taps:
        show_status("✅ Access Granted. Gate Opening...", "#00FF7F")
        open_gate()
        door_duration = 15
        for i in range(door_duration, 0, -1):
            update_door_info(i)
            time.sleep(1)
            root.update()
        close_gate()
        door_info_label.config(text="")
        show_status("🔒 Gate Closed. Ready for next user.", "gray")
    else:
        show_status(f"❌ Access Denied. Detected {final_tap_count}.", "red")

#  MAIN BUTTON 
main_button = tk.Button(root, text="Request Access", command=main_button_handler,
                        width=25, height=3, bg="#1E90FF", fg="white", font=button_font)
main_button.pack(pady=30)

root.mainloop()
