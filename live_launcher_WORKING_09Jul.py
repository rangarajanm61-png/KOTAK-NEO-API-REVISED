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
            restart_main()
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
    spot_process = subprocess.Popen(["python3", "nifty_index_live_test.py"])


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

    main_process = subprocess.Popen(["python3", "main.py"], env=env)


print("=" * 55)
print("        KOTAK NEO LIVE SYSTEM V3.2")
print("=" * 55)

print("\nSTEP 1 : LOGIN")
login_result = subprocess.run(["python3", "login_once.py"])
if login_result.returncode != 0:
    print("❌ Login failed. Stop.")
    raise SystemExit

print("\nSTEP 2 : SELECT EXPIRY")

print("\nOpen main.py expiry list reference:")
print("1. 04Aug2026")
print("2. 11Aug2026")
print("3. 14Jul2026")
print("4. 21Jul2026")
print("5. 24Dec2029")
print("6. 24Jun2031")
print("7. 25Aug2026")
print("8. 25Jun2030")
print("9. 26Dec2028")
print("10. 26Jun2029")
print("11. 27Jun2028")
print("12. 28Dec2027")
print("13. 28Jul2026")
print("14. 29Dec2026")
print("15. 29Jun2027")
print("16. 29Sep2026")
print("17. 30Mar2027")
print("18. 31Dec2030")

expiry = input("Enter Expiry Number: ").strip()

with open("selected_expiry.txt", "w") as f:
    f.write(expiry)

print(f"Selected Expiry Number saved: {expiry}")

def show_file_time(label, file_name):
    if os.path.exists(file_name):
        t = datetime.fromtimestamp(os.path.getmtime(file_name))
        print(f"{label} updated time : {t.strftime('%d-%b-%Y %H:%M:%S')}")
    else:
        print(f"{label} not found.")

print("\nSTEP 3 : MORNING OI MAINTENANCE")

ans = input("Refresh Closing OI from Neo now? (Y/N): ").strip().lower()

if ans == "y":
    print("\nRefreshing Closing OI from Neo...")

    env = os.environ.copy()
    env["LAUNCHER_MODE"] = "1"
    main_process = subprocess.Popen(["python3", "main.py"], env=env)

    print("Waiting 60 seconds for main.py to create latest closing OI file...")
    time.sleep(60)

    if main_process.poll() is None:
        main_process.terminate()
        main_process.wait()
    else:
        print("✓ main.py finished normally.")

    if os.path.exists(CLOSING_FILE):
        print("✓ Closing OI file refreshed.")
    else:
        print("✗ Closing OI file not found after refresh.")
else:
    print("Existing Closing OI retained.")

show_file_time("Closing OI file", CLOSING_FILE)

ans2 = input("Update Opening Baseline from Closing file? (Y/N): ").strip().lower()

if ans2 == "y":
    print("\n⚠️ MANUAL EXPIRY CHECK")
    print(f"Selected Expiry : {expiry}")
    print("Confirm closing file belongs to SAME expiry.")

    confirm = input("Proceed with update? (Y/N): ").strip().lower()

    if confirm == "y":
        if os.path.exists(CLOSING_FILE):
            shutil.copy(CLOSING_FILE, OPENING_FILE)
            print("✓ Opening baseline updated.")
        else:
            print("✗ Closing file not found.")
    else:
        print("✗ Opening baseline update cancelled.")
else:
    print("Existing opening baseline retained.")

show_file_time("Opening baseline file", OPENING_FILE)
    
print("\nSTEP 4 : START LIVE FEED")
live_process = subprocess.Popen(["python3", "live_feed.py"])

print("\nSTEP 5 : START NIFTY SPOT")
spot_process = subprocess.Popen(["python3", "nifty_index_live_test.py"])

if not wait_for_spot():
    raise SystemExit

print("\nSTEP 6 : START MAIN")
env = os.environ.copy()
env["LAUNCHER_MODE"] = "1"
main_process = subprocess.Popen(["python3", "main.py"], env=env)

if not wait_for_option_chain():
    raise SystemExit

print("\nSTEP 7 : START DASHBOARD")

while True:

    print("\nAvailable ports : 8502  8503  8504", flush=True)

    print(">>> STEP 6 INPUT IS PORT NUMBER, NOT TOTP <<<", flush=True)
    port = input("Enter PORT No for dashboard [8502 / 8503 / 8504]: ").strip()

    if port == "":
        port = "8502"

    if not port.isdigit():
        print("❌ Port must be numeric.")
        continue

    port_num = int(port)

    if port_num < 1024 or port_num > 65535:
        print("❌ Invalid port.")
        continue

    dashboard_process = subprocess.Popen([
        "streamlit",
        "run",
        "dashboard2.py",
        "--server.port",
        str(port_num)
    ])

    print(f"\nDashboard launch requested on port {port_num}.")
    print("Waiting for dashboard to start...")
    time.sleep(5)

    if dashboard_process.poll() is None:
        print(f"\n✓ Dashboard started on port {port_num}")
        break

    print(f"\n❌ Dashboard failed on port {port_num}")
    print("1. Retry same port")
    print("2. Enter another port")
    print("3. Exit")

    choice = input("Choose (1/2/3): ").strip()

    if choice == "1":
        continue

    elif choice == "2":
        continue

    else:
        raise SystemExit("Launcher stopped.")

print("\n" + "=" * 55)
print("        SYSTEM READY FOR TRADING")
print("=" * 55)
print("✓ Login")
print("✓ Spot Live")
print("✓ Option Chain Live")
print(f"✓ Dashboard Started on port {port}")
print(f"✓ Time: {datetime.now().strftime('%H:%M:%S')}")
print("=" * 55)

dashboard_process.wait()