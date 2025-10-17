import serial, time

SERIAL_PORT = "COM3"  # Change to your Arduino port
BAUD_RATE = 9600

try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=2)
    time.sleep(2)
    print("✅ Connected to Arduino")
except Exception as e:
    print("❌ Serial connection failed:", e)
    ser = None

def start_tap_window():
    """Ask Arduino to detect taps within 10 seconds."""
    if not ser:
        return 0
    ser.reset_input_buffer()
    ser.write(b"START_TAP\n")
    start = time.time()
    tap_count = 0
    while time.time() - start < 10:  # Increased to 10 sec
        line = ser.readline().decode(errors="ignore").strip()
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
    if ser:
        ser.write(b"OPEN\n")

def close_gate():
    if ser:
        ser.write(b"CLOSE\n")
