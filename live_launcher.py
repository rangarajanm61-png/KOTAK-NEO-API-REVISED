import os
import time
import shutil
import subprocess
import pandas as pd
from datetime import datetime

SPOT_FILE = "nifty_spot_live.txt"
OPTION_FILE = "option_chain.csv"
CLOSING_FILE = "option_chain_base_oi_closing.csv"
OPENING_FILE = "option_chain_base_oi_opening.csv"

spot_process = None
main_process = None
dashboard_process = None


def wait_for_spot(timeout=45):
    while True:
        start = time.time()
        while time.time() - start < timeout:
            try:
                with open(SPOT_FILE, "r") as f:
                    spot = float(f.read().strip())
                if spot > 0:
                    print(f"✓ Spot live: {spot}")
                    return True
            except Exception:
                pass
            time.sleep(2)

        print("\n❌ Spot not received within time.")
        print("1. Wait again")
        print("2. Restart spot reader")
        print("3. Exit")
        choice = input("Choose: ").strip()

        if choice == "1":
            continue
        elif choice == "2":
            restart_spot_reader()
        else:
            return False


def wait_for_option_chain(timeout=90):
    while True:
        start = time.time()
        while time.time() - start < timeout:
            try:
                df = pd.read_csv(OPTION_FILE)
                if len(df) > 0:
                    print(f"✓ Option chain live: {len(df)} rows")
                    return True
            except Exception:
                pass
            time.sleep(3)

        print("\n❌ option_chain.csv not updated within time.")
        print("1. Wait again")
        print("2. Restart main.py")
        print("3. Exit")
        choice = input("Choose: ").strip()

        if choice == "1":
            continue
        elif choice == "2":
            print("Automatic restart disabled. Start main.py manually.")
            return False
        else:
            return False


def restart_spot_reader():
    global spot_process
    try:
        if spot_process:
            spot_process.terminate()
    except Exception:
        pass

    print("Restarting spot reader...")
    spot_process = subprocess.Popen(["python3", "nifty_index_live.py"])


def restart_main():
    global main_process
    try:
        if main_process:
            main_process.terminate()
    except Exception:
        pass

    print("Restarting main.py...")
    env = os.environ.copy()
    env["LAUNCHER_MODE"] = "1"
    
    main_process = subprocess.Popen(
        ["python3", "main.py"],
        env=env
    )


print("=" * 55)
print("        KOTAK NEO LIVE SYSTEM V3.2")
print("=" * 55)

print("\nSTEP 1 : LOGIN")
login_result = subprocess.run(["python3", "login_once.py"])
if login_result.returncode != 0:
    print("❌ Login failed. Stop.")
    raise SystemExit

print("\nSTEP 2 : SELECT EXPIRY")

expiry_list = [
    "04Aug2026",
    "11Aug2026",
    "14Jul2026",
    "21Jul2026",
    "24Dec2029",
    "24Jun2031",
    "25Aug2026",
    "25Jun2030",
    "26Dec2028",
    "26Jun2029",
    "27Jun2028",
    "28Dec2027",
    "28Jul2026",
    "29Dec2026",
    "29Jun2027",
    "29Sep2026",
    "30Mar2027",
    "31Dec2030",
]

for i, expiry_date in enumerate(expiry_list, start=1):
    print(f"{i}. {expiry_date}")

while True:
    expiry_number = input("Enter Expiry Number: ").strip()

    if not expiry_number.isdigit():
        print("Please enter a valid number.")
        continue

    expiry_index = int(expiry_number) - 1

    if 0 <= expiry_index < len(expiry_list):
        selected_expiry = expiry_list[expiry_index]
        break

    print(f"Please enter a number from 1 to {len(expiry_list)}.")

with open("selected_expiry.txt", "w") as f:
    f.write(selected_expiry)

print(f"Selected Expiry Number: {expiry_number}")
print(f"Selected Expiry Date saved: {selected_expiry}")

def show_file_time(label, file_name):
    if os.path.exists(file_name):
        t = datetime.fromtimestamp(os.path.getmtime(file_name))
        print(f"{label} updated time : {t.strftime('%d-%b-%Y %H:%M:%S')}")
    else:
        print(f"{label} not found.")

print("\nSTEP 3 : START NIFTY SPOT")
spot_process = subprocess.Popen(
    ["python3", "nifty_index_live.py"]
)

print("STEP 3 COMPLETED: NIFTY spot started.")

print("\nSTEP 4 : START MAIN")

env = os.environ.copy()
env["LAUNCHER_MODE"] = "1"

main_process = subprocess.Popen(
    ["python3", "main.py"],
    env=env
)

print("STEP 4 COMPLETED: main.py started.")

print("\n" + "=" * 55)
print("        SYSTEM READY FOR DASH BOARD OPENING")
print("=" * 55)
print("✓ Login")
print("✓ Spot Live")
print("✓ Option Chain Live")
# print(f"✓ Dashboard Started on port {port}")
print(f"✓ Time: {datetime.now().strftime('%H:%M:%S')}")
print("=" * 55)

# dashboard_process.wait()
print("\nLauncher will remain active.")
print("Press Ctrl+C to stop all live processes.")

try:
    while True:
        time.sleep(60)
except KeyboardInterrupt:
    print("\nLive launcher stopped.")