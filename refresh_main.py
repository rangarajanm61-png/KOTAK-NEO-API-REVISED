import subprocess
import time
from datetime import datetime

while True:
    print("Running main.py at", datetime.now().strftime("%H:%M:%S"))


    subprocess.run(["python", "main.py"])

    print("Waiting 30 seconds...\n")
    time.sleep(30)