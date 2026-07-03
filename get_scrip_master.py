from neo_api_client import NeoAPI
from dotenv import load_dotenv
import os
import time
from datetime import datetime, timedelta
from datetime import time as dt_time
from option_chain import (
    calculate_pcr,
    calculate_greeks,
    get_time_to_expiry,
    calculate_iv,
    calculate_decay,
)
load_dotenv()
consumer_key = os.getenv("CONSUMER_KEY")

client = NeoAPI(
    consumer_key=consumer_key,
    environment="prod"
)

mobile = os.getenv("MOBILE_NUMBER")
ucc = os.getenv("UCC")
totp = input("Enter TOTP from authenticator app: ")

response = client.totp_login(
    mobile_number="+91" + str(mobile),
    ucc=ucc,
    totp=totp
)

print("Login response:", response)

mpin = os.getenv("MPIN")

validate_response = client.totp_validate(
    mpin=mpin
)

print("2FA response:", validate_response)
print("\n================================")
print("LOGIN SUCCESSFUL")
print("--------------------------------\n")

print("Downloading NSE master...")

url = client.scrip_master(exchange_segment="nse_cm")
print(url)

import pandas as pd

df = pd.read_csv(url)

print(df.columns.tolist())
print(df.head())
print("\nSearching for NIFTY...\n")

result = df[
    df["pSymbolName"].astype(str).str.contains("NIFTY", case=False, na=False)
    |
    df["pTrdSymbol"].astype(str).str.contains("NIFTY", case=False, na=False)
]

print(result[[
    "pSymbol", "pSymbolName", "pTrdSymbol",
    "pExchSeg", "pInstName", "pGroup",
    "pAssetCode", "pSubGroup"
]].head(20).to_string())

for seg in ["nse_cm", "nse_fo", "nse_idx", "nse_index", "indices"]:
    try:
        print("\nSEGMENT:", seg)
        url = client.scrip_master(exchange_segment=seg)
        print(url)
    except Exception as e:
        print("ERROR:", e)