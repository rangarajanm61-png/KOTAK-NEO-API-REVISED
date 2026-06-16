from neo_api_client import NeoAPI
from dotenv import load_dotenv
import os
from option_chain import calculate_pcr
from option_chain import calculate_greeks
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

# data = client.search_scrip(
#     exchange_segment="nse_cm",
#     symbol="NIFTY"
# )

import pandas as pd

option = client.search_scrip(
    exchange_segment="nse_fo",
    symbol="NIFTY"
)

raw_option = option.get("data", option) if isinstance(option, dict) else option
option_df = pd.DataFrame(raw_option if isinstance(raw_option, list) else [raw_option])

# Keep only NIFTY CE/PE options

option_df = option_df[
    (option_df["pInstType"] == "OPTIDX") &
    (option_df["pSymbolName"].astype(str).eq("NIFTY")) &
    (option_df["pOptionType"].isin(["CE", "PE"]))
].copy()

print("NIFTY option rows =", len(option_df))
# print(option_df["pTrdSymbol"].head(20))
# exit()

# print("\n========== OPTION SYMBOLS ==========")

# print(option_df.head(20).to_string(index=False))

# print("\n========== END OPTION SYMBOLS ==========")

# print("\n===================================")
# print("NIFTY OPTION CONTRACTS")
# print("===================================")

# print("Rows Found :", len(option_df))

# print("\nColumns Available:")
# print(option_df.columns.tolist())

# print("\nFirst 10 Records:")
# print(option_df.head(10).to_string(index=False))

# # PCR quick check using available option symbols
# print("\nNIFTY OPTION DATA READY")
# print("Total option rows:", len(option_df))

# print(option_df.head(20).to_string(index=False))
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
option_df = pd.DataFrame(option)

# Extract strike from symbol
option_df["Strike"] = (
    option_df["pTrdSymbol"]
    .str.extract(r"(\d{5})(?=CE|PE)")
)

# Remove rows where strike not found
option_df = option_df.dropna(subset=["Strike"])

# Convert to integer
option_df["Strike"] = option_df["Strike"].astype(int)

option_cols = [
    "Strike",
    "pOptionType",
    "pTrdSymbol",
    "pExpiryDate",
    "pSymbol"
]

# print("\nROWS =", len(option_df))

# print("\nCOLUMNS =")
# print(option_df.columns.tolist())

# print(
#     option_df[
#         ["pTrdSymbol",
#          "pOptionType",
#          "pExpiryDate"]
#     ].head(20)
# )

# print("\nNIFTY OPTION DATA")
# print(option_df[option_cols].to_string(index=False))

# Find 23300 CE for 09Jun2026
# sample_option = option_df[
#    (option_df["Strike"] == 23300) &
#    (option_df["pOptionType"] == "CE") &
#    (option_df["pExpiryDate"] == selected_expiry)
#]

# print("\nSELECTED OPTION")
# print(sample_option[["pTrdSymbol", "pOptionType", "pExpiryDate", "pSymbol"]].to_string(index=False)) # type: ignore

# Dynamic strike range

spot = float(input("Enter current NIFTY spot: "))

atm = round(spot / 50) * 50
lower_strike = atm - 1000
upper_strike = atm + 1000

print("SELECTED EXPIRY =", selected_expiry)
# print(option_df[["Strike", "pOptionType", "pExpiryDate", "pTrdSymbol", "pSymbol"]].head(30))
ltp_df = option_df[
    (option_df["Strike"] >= lower_strike) &
    (option_df["Strike"] <= upper_strike) &
    (option_df["pExpiryDate"] == selected_expiry) &
    (option_df["pTrdSymbol"].astype(str).str.contains("NIFTY26", na=False)) &
    (~option_df["pTrdSymbol"].astype(str).str.contains("MIDCPNIFTY|FINNIFTY|BANKNIFTY", na=False)) &
    (option_df["pOptionType"].isin(["CE", "PE"]))
][["Strike", "pOptionType", "pTrdSymbol", "pSymbol"]].copy()

# print("ATM OPTIONS FOUND")
# print(
#    ltp_df[["Strike","pOptionType","pSymbol"]]
#)
# print("LTP DF ROWS =", len(ltp_df))
# print(ltp_df[["Strike","pOptionType","pSymbol"]])
# exit()

ltp_rows = []

for _, row in ltp_df.iterrows():

    token = str(row["pSymbol"])
    
    ltp_data = client.quotes(
       
    instrument_tokens=[{

        "exchange_segment": "nse_fo",
        "instrument_token": token
    }],
    quote_type="all"
)
    
    if not isinstance(ltp_data, list) or len(ltp_data) == 0:
        print("QUOTE FAILED, SKIPPING TOKEN =", token, ltp_data)
        continue
    
    ltp_value = ltp_data[0]["ltp"]

    ltp_rows.append({
    "Token": int(token),
    "Strike": int(row["Strike"]),
    "Type": str(row["pOptionType"]).upper().strip(),
    "LTP": float(ltp_data[0].get("ltp", 0)),
    "OI": int(ltp_data[0].get("open_int", 0) or 0),
    "Volume": int(ltp_data[0].get("last_volume", 0) or 0),
    })
    
final_ltp_df = pd.DataFrame(ltp_rows)


# Convert into option-chain format

final_ltp_df["Type"] = final_ltp_df["Type"].astype(str).str.upper().str.strip()
# print(final_ltp_df[["Strike", "Type", "LTP", "OI", "Volume"]].head(20))

ce_df = final_ltp_df[
    final_ltp_df["Type"] == "CE"
][["Strike", "LTP", "OI", "Volume"]]

# print(ltp_rows[:5])

ce_df.columns = ["Strike", "CE_LTP", "CE OI", "CE Volume"]

pe_df = final_ltp_df[
    final_ltp_df["Type"] == "PE"
][["Strike", "LTP", "OI", "Volume"]]

pe_df.columns = ["Strike", "PE_LTP", "PE OI", "PE Volume"]

option_chain = pd.merge(
    ce_df,
    pe_df,
    on="Strike",
    how="outer"
)

option_chain = option_chain.fillna(0)

option_chain["OI PCR"] = option_chain.apply(
    lambda r: round(r["PE OI"] / r["CE OI"], 2) if r["CE OI"] != 0 else 0,
    axis=1
)

option_chain["Vol PCR"] = option_chain.apply(
    lambda r: round(r["PE Volume"] / r["CE Volume"], 2) if r["CE Volume"] != 0 else 0,
    axis=1
)

ce_oi_total = option_chain["CE OI"].sum()
pe_oi_total = option_chain["PE OI"].sum()

ce_vol_total = option_chain["CE Volume"].sum()
pe_vol_total = option_chain["PE Volume"].sum()

overall_oi_pcr = round(pe_oi_total / ce_oi_total, 2) if ce_oi_total != 0 else 0
overall_vol_pcr = round(pe_vol_total / ce_vol_total, 2) if ce_vol_total != 0 else 0

option_chain["Expiry"] = selected_expiry
option_chain["Spot"] = spot

option_chain.to_csv("option_chain.csv", index=False)
print("option_chain.csv saved")

# Step 4: ATM / ITM / OTM identification

option_chain["Distance"] = abs(
    option_chain["Strike"] - spot
)

atm_strike = round(spot / 50) * 50

option_chain["Status"] = option_chain["Strike"].apply(
    lambda x: "ATM" if x == atm_strike else
              "ITM CE / OTM PE" if x < spot else
              "OTM CE / ITM PE"
)
# print("\nNIFTY OPTION CHAIN WITH STATUS")

# print(option_chain[[
#     "Strike",
#     "CE_LTP",
#     "PE_LTP",
#     "CE OI",
#     "PE OI",
#     "OI PCR",
#     "CE Volume",
#     "PE Volume",
#     "Vol PCR",
#     "Expiry",
#     "Spot",
#     "Distance",
#     "Status"
# ]].to_string(index=False))

# print("\nATM Strike =", atm_strike)

# ATM CE / PE token extraction for live_feed.py

atm_ce = option_df[
    (option_df["Strike"] == atm_strike) &
    (option_df["pOptionType"] == "CE") &
    (option_df["pExpiryDate"] == selected_expiry)
]

atm_pe = option_df[
    (option_df["Strike"] == atm_strike) &
    (option_df["pOptionType"] == "PE") &
    (option_df["pExpiryDate"] == selected_expiry)
]

# print("\nATM CE TOKEN")
# print(atm_ce[["pTrdSymbol", "pSymbol"]].to_string(index=False))

# print("\nATM PE TOKEN")
# print(atm_pe[["pTrdSymbol", "pSymbol"]].to_string(index=False))

ce_token = str(atm_ce.iloc[0]["pSymbol"])
pe_token = str(atm_pe.iloc[0]["pSymbol"])

print("\nCE TOKEN =", ce_token)
print("PE TOKEN =", pe_token)

with open("tokens.txt", "w") as f:
    for t in final_ltp_df["Token"].dropna().unique():
        f.write(str(int(t)) + "\n")
    

print("Tokens saved to tokens.txt")

# print(option_chain.to_string(index=False))
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

if not option_chain.empty:
    option_chain["Trading_Bias"] = option_chain.apply(
        trading_bias,
        axis=1
    )
else:
    option_chain["Trading_Bias"] = ""

# print("\nTOP 3 CE SELL CANDIDATES")
# print(
#     option_chain[
#         option_chain["Trading_Bias"].str.contains("CE Sell", na=False)
#     ][["Strike", "CE_TimeValue", "Trading_Bias"]]
#     .sort_values("CE_TimeValue", ascending=False)
#     .head(3)
#     .to_string(index=False)
# )

# print("\nTOP 3 PE SELL CANDIDATES")
# print(
#     option_chain[
#         option_chain["Trading_Bias"].str.contains("PE Sell", na=False)
#     ][["Strike", "PE_TimeValue", "Trading_Bias"]]
#     .sort_values("PE_TimeValue", ascending=False)
#     .head(3)
#     .to_string(index=False)
# )
print("\nNIFTY OPTION CHAIN WITH STATUS AND TRADING BIAS")

print(
    option_chain[[
        "Strike",
        "CE_LTP",
        "PE_LTP",
        "CE OI",
        "PE OI",
        "OI PCR",
        "CE Volume",
        "PE Volume",
        "Vol PCR",
        "Expiry",
        "Spot",
        "Distance",
        "Status",
        "CE_TimeValue",
        "PE_TimeValue",
        "Trading_Bias"
    ]].to_string(index=False)
)
print("\nOVERALL PCR")
print("Overall OI PCR  =", overall_oi_pcr)
print("Overall Vol PCR =", overall_vol_pcr)