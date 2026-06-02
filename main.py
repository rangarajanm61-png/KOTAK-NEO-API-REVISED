from neo_api_client import NeoAPI
from dotenv import load_dotenv
import os

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
print("================================\n")

data = client.search_scrip(
    exchange_segment="nse_cm",
    symbol="NIFTY"
)

data = client.search_scrip(
    exchange_segment="nse_cm",
    symbol="NIFTY"
)

import pandas as pd

data = client.search_scrip(
    exchange_segment="nse_cm",
    symbol="NIFTY 50"
)

df = pd.DataFrame([data])
print(df.columns.tolist())

# Show only useful columns
cols = ['pSymbolName', 'pTrdSymbol', 'pSymbol', 'pExchSeg']

available_cols = [c for c in cols if c in df.columns]

print("\nNIFTY CASH DATA")
print(df[available_cols].to_string(index=False))


option = client.search_scrip(
    exchange_segment="nse_fo",
    symbol="NIFTY"
)

option_df = pd.DataFrame(option)

# Filter only NIFTY options
option_df = option_df[option_df["pSymbolName"] == "NIFTY"]

# Only option contracts (not futures)
option_df = option_df[option_df["pInstName"] == "OPTIDX"]

# Select expiry date

expiry_list = sorted(option_df["pExpiryDate"].dropna().unique())

print("\nAvailable Expiry Dates:")
for i, exp in enumerate(expiry_list, start=1):
    print(i, exp)

choice = int(input("Select expiry number: "))
selected_expiry = expiry_list[choice - 1]

print("Selected Expiry =", selected_expiry)

option_df = option_df[
    option_df["pExpiryDate"] == selected_expiry
]

# Extract strike from symbol
option_df["Strike"] = option_df["pTrdSymbol"].str.extract(r'(\d{5})(?=CE|PE)').astype(int)

option_cols = [
    "Strike",
    "pOptionType",
    "pTrdSymbol",
    "pExpiryDate",
    "pSymbol"
]

print("\nNIFTY OPTION DATA")
print(option_df[option_cols].to_string(index=False))
# Find 23800 CE for 02Jun2026
sample_option = option_df[
    (option_df["Strike"] == 23800) &
    (option_df["pOptionType"] == "CE") &
    (option_df["pExpiryDate"] == "02Jun2026")
]

print("\nSELECTED OPTION")
print(sample_option.to_string(index=False))

# Dynamic strike range

spot = float(input("Enter current NIFTY spot: "))

atm = round(spot / 50) * 50
lower_strike = atm - 300
upper_strike = atm + 300

ltp_df = option_df[
    (option_df["Strike"] >= lower_strike) &
    (option_df["Strike"] <= upper_strike) &
    (option_df["pExpiryDate"] == selected_expiry) &
    (option_df["pOptionType"].isin(["CE", "PE"]))
].copy()

ltp_rows = []

for _, row in ltp_df.iterrows():

    token = str(row["pSymbol"])

    ltp_data = client.quotes(
        instrument_tokens=[{
            "exchange_segment": "nse_fo",
            "instrument_token": token
        }],
        quote_type="ltp"
    )

    ltp_value = ltp_data[0]["ltp"]

    ltp_rows.append({
        "Strike": int(row["Strike"]),
        "Type": row["pOptionType"],
        "LTP": ltp_value
    })

final_ltp_df = pd.DataFrame(ltp_rows)

# Convert into option-chain format
ce_df = final_ltp_df[
    final_ltp_df["Type"] == "CE"
][["Strike", "LTP"]]

ce_df.columns = ["Strike", "CE_LTP"]

pe_df = final_ltp_df[
    final_ltp_df["Type"] == "PE"
][["Strike", "LTP"]]

pe_df.columns = ["Strike", "PE_LTP"]

option_chain = pd.merge(
    ce_df,
    pe_df,
    on="Strike"
)

option_chain = option_chain.sort_values(
    by="Strike"
)

print("\nNIFTY OPTION CHAIN")
print(option_chain.to_string(index=False))
# Step 4: ATM / ITM / OTM identification

# spot already defined above

option_chain["Distance"] = abs(
    option_chain["Strike"] - spot
)

atm_strike = round(spot / 50) * 50

option_chain["Status"] = option_chain["Strike"].apply(
    lambda x: "ATM" if x == atm_strike else
              "ITM CE / OTM PE" if x < spot else
              "OTM CE / ITM PE"
)

print("\nATM Strike =", atm_strike)

print("\nNIFTY OPTION CHAIN WITH STATUS")
print(option_chain.to_string(index=False))
# Convert LTP columns to numeric

option_chain["CE_LTP"] = pd.to_numeric(
    option_chain["CE_LTP"],
    errors="coerce"
)

option_chain["PE_LTP"] = pd.to_numeric(
    option_chain["PE_LTP"],
    errors="coerce"
)
# Step 5: Intrinsic Value & Time Value

# Correct intrinsic values

option_chain["CE_Intrinsic"] = option_chain["Strike"].apply(
    lambda x: max(spot - x, 0)
)

option_chain["PE_Intrinsic"] = option_chain["Strike"].apply(
    lambda x: max(x - spot, 0)
)

# Time value (never negative)

option_chain["CE_TimeValue"] = (
    option_chain["CE_LTP"] -
    option_chain["CE_Intrinsic"]
).clip(lower=0).round(2)

option_chain["PE_TimeValue"] = (
    option_chain["PE_LTP"] -
    option_chain["PE_Intrinsic"]
).clip(lower=0).round(2)

def trading_bias(row):

    # ATM
    if row["Status"] == "ATM":
        return "ATM High Theta"

    # CE side
    if "ITM CE" in row["Status"]:

        if row["CE_TimeValue"] > 150:
            return "CE Sell Strong"

        elif row["CE_TimeValue"] > 75:
            return "CE Sell"

        else:
            return "CE Buy"

    # PE side
    if "ITM PE" in row["Status"]:

        if row["PE_TimeValue"] > 150:
            return "PE Sell Strong"

        elif row["PE_TimeValue"] > 75:
            return "PE Sell"

        else:
            return "PE Buy"

    return "Neutral"

option_chain["Trading_Bias"] = option_chain.apply(
    trading_bias,
    axis=1
)
print("\nTOP 3 CE SELL CANDIDATES")
print(
    option_chain[
        option_chain["Trading_Bias"].str.contains("CE Sell", na=False)
    ][["Strike", "CE_TimeValue", "Trading_Bias"]]
    .sort_values("CE_TimeValue", ascending=False)
    .head(3)
    .to_string(index=False)
)

print("\nTOP 3 PE SELL CANDIDATES")
print(
    option_chain[
        option_chain["Trading_Bias"].str.contains("PE Sell", na=False)
    ][["Strike", "PE_TimeValue", "Trading_Bias"]]
    .sort_values("PE_TimeValue", ascending=False)
    .head(3)
    .to_string(index=False)
)
print("\nNIFTY OPTION CHAIN WITH TRADING BIAS")
print(
    option_chain[
        [
            "Strike",
            "CE_LTP",
            "PE_LTP",
            "Status",
            "CE_TimeValue",
            "PE_TimeValue",
            "Trading_Bias"
        ]]
    .to_string(index=False)
)