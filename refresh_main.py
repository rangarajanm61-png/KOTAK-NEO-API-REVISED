import time
import os

while True:
    print("Running main.py to refresh option_chain.csv")
    os.system("python main.py")
    print("Waiting 5 seconds...")
    time.sleep(5)