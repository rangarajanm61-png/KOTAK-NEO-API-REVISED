# Login once
# Subscribe NIFTY option tokens
# Receive live LTP update
# Print live CE/PE values
from neo_api_client import NeoAPI
from dotenv import load_dotenv
import os
import time
from datetime import datetime

load_dotenv()

consumer_key = os.getenv("CONSUMER_KEY")
mobile = os.getenv("MOBILE_NUMBER")
ucc = os.getenv("UCC")
mpin = os.getenv("MPIN")

client = NeoAPI(
    consumer_key=consumer_key,
    environment="prod"
)

totp = input("Enter TOTP from authenticator app: ")

response = client.totp_login(
    mobile_number="+91" + str(mobile),
    ucc=ucc,
    totp=totp
)

print("Login response:", response)

validate_response = client.totp_validate(
    mpin=mpin
)

print("2FA response:", validate_response)
print("LOGIN SUCCESSFUL")

def on_message(message):
    # print("RAW INDEX TICK =", message)

    try:
        data = message.get("data", [])
        if data:
            tick = data[0]
            spot = tick.get("ltp") or tick.get("last_price") or tick.get("ltpPrice") or tick.get("c")

            if spot:
                with open("nifty_spot_live.txt", "w") as f:
                    f.write(str(spot))

                print("NIFTY SPOT SAVED =", spot)

    except Exception as e:
        print("SPOT SAVE ERROR =", e)

def on_error(error):
    print("INDEX ERROR =", error)

def on_open(message):
    print("INDEX WEBSOCKET OPENED =", message)

client.on_message = on_message
client.on_error = on_error
client.on_open = on_open

client.subscribe(
    instrument_tokens=[{
        "instrument_token": "26000",
        "exchange_segment": "nse_cm"
    }],
    isIndex=False,
    isDepth=False
)


print("Subscribed NIFTY index. Waiting for live ticks...")

while True:
    time.sleep(1)