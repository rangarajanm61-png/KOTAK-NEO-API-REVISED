# Login once
# Subscribe NIFTY option tokens
# Receive live LTP update
# Print live CE/PE values
from neo_api_client import NeoAPI
from dotenv import load_dotenv
import os
import time

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
    try:
        data = message.get("data", [])
        for tick in data:
            token = tick.get("tk")
            symbol = tick.get("ts")
            ltp = tick.get("ltp")
            volume = tick.get("v")
            oi = tick.get("oi")

            print(f"TOKEN={token} SYMBOL={symbol} LTP={ltp} VOL={volume} OI={oi}")

    except Exception as e:
        print("LIVE DATA:", message)
        print("PARSE ERROR:", e)

def on_error(error):
    print("ERROR:", error)

def on_close(message):
    print("CLOSED:", message)

def on_open(message):
    print("WEBSOCKET OPENED:", message)

client.on_message = on_message
client.on_error = on_error
client.on_close = on_close
client.on_open = on_open

# Test one NIFTY option token first
tokens = [
    {
        "instrument_token": "42301",
        "exchange_segment": "nse_fo"
    }
]

client.subscribe(
    instrument_tokens=tokens,
    isIndex=False,
    isDepth=False
)

print("Subscribed. Waiting for live ticks...")

while True:
    time.sleep(1)