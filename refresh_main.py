import time
import os

while True:
    print("Running main.py to refresh option_chain.csv")
    os.system("/home/codespace/.python/current/bin/python main_backup_working_13Jun.py")
    print("Waiting 5 seconds...")
    time.sleep(5)