from neo_api_client import NeoAPI
from dotenv import load_dotenv
import os
from option_chain import calculate_pcr, calculate_greeks, get_time_to_expiry
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
# print(df.columns.tolist())

# Show only useful columns
cols = ['pSymbolName', 'pTrdSymbol', 'pSymbol', 'pExchSeg']

available_cols = [c for c in cols if c in df.columns]

# print("\nNIFTY CASH DATA")
# print(df[available_cols].to_string(index=False))

option = client.search_scrip(
    exchange_segment="nse_fo",
    symbol="NIFTY"
)

option_df = pd.DataFrame(option)
# print("\nROWS =", len(option_df))
# print("\nCOLUMNS =")
# print(option_df.columns.tolist())
# print("\nCOLUMNS AVAILABLE:")
# print(option_df.columns.tolist())

# print("\n========== OPTION SYMBOLS ==========")

# print(
#     option_df[
#         ["pSymbolName","pTrdSymbol"]
#     ].head(20).to_string(index=False)
# )
# print("\n========== END OPTION SYMBOLS ==========")

# Filter only NIFTY options
# option_df = option_df[option_df["pSymbolName"] == "NIFTY"]

# Only option contracts (not futures)
# option_df = option_df[option_df["pInstName"] == "OPTIDX"]

# print("\n===================================")
# print("NIFTY OPTION CONTRACTS")
# print("===================================")

# print("Rows Found :", len(option_df))

# print("\nColumns Available:")
# print(option_df.columns.tolist())

# print("\nFirst 10 Records:")
# print(option_df.head(10).to_string(index=False))

# PCR quick check using available option symbols
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
sample_option = option_df[
    (option_df["Strike"] == 23300) &
    (option_df["pOptionType"] == "CE") &
    (option_df["pExpiryDate"] == selected_expiry)
]

# print("\nSELECTED OPTION")
# print(sample_option[["pTrdSymbol", "pOptionType", "pExpiryDate", "pSymbol"]].to_string(index=False))

# Dynamic strike range
# try:
#     nifty_search = client.search_scrip(
#         exchange_segment="nse_cm",
#         symbol="NIFTY"
#     )
#     print("NIFTY SEARCH RAW =", nifty_search)
# except Exception as e:
#     print("NIFTY SEARCH ERROR =", e)

# spot = float(input("Enter current NIFTY spot: "))

# Auto NIFTY using current month futures as proxy
fut_master = pd.DataFrame(client.search_scrip(
    exchange_segment="nse_fo",
    symbol="NIFTY"
))

nifty_fut = fut_master[
    fut_master["pTrdSymbol"].astype(str).str.contains("NIFTY26JUNFUT", na=False)
]

# print("NIFTY FUT ROW =")
# print(nifty_fut[["pTrdSymbol", "pSymbol"]].head().to_string(index=False))

fut_token = str(nifty_fut.iloc[0]["pSymbol"])

fut_data = client.quotes(
    instrument_tokens=[{
        "exchange_segment": "nse_fo",
        "instrument_token": fut_token
    }],
    quote_type="all"
)

spot = float(fut_data[0]["ltp"])
print("AUTO NIFTY FUT PROXY =", spot)

atm = round(spot / 50) * 50
lower_strike = atm - 500
upper_strike = atm + 500

ltp_df = option_df[
    (option_df["Strike"] >= lower_strike) &
    (option_df["Strike"] <= upper_strike) &
    (option_df["pExpiryDate"] == selected_expiry) &
    (option_df["pOptionType"].isin(["CE", "PE"]))
].copy()

# print("LTP_DF_ROWS =", len(ltp_df))
# print(ltp_df[["Strike","pOptionType"]].head(20))

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
    
# print("TOKEN =", token)
# print("LTP =", ltp_data[0].get("ltp"))

# print("LAST TRADED QTY =", ltp_data[0].get("last_traded_quantity"))
# print("LAST VOLUME =", ltp_data[0].get("last_volume"))

# print("TOTAL BUY =", ltp_data[0].get("total_buy"))
# print("TOTAL SELL =", ltp_data[0].get("total_sell"))

# print("DEPTH =", ltp_data[0].get("depth"))

# ltp_value = ltp_data[0]["ltp"]

    ltp_row = ltp_data[0] if isinstance(ltp_data, list) and len(ltp_data) > 0 else {}

ltp_rows.append({
    "Strike": int(row["Strike"]),
    "Type": row.get("OptionType", row.get("Type", "")),
    "LTP": float(ltp_row.get("ltp", 0) or 0),
    "PriceChange": float(ltp_row.get("change", 0) or 0),
    "PricePctChange": float(ltp_row.get("per_change", 0) or 0),
    "OI": int(ltp_row.get("open_int", 0) or 0),
    "Volume": int(ltp_row.get("last_volume", 0) or 0),
})

final_ltp_df = pd.DataFrame(ltp_rows)

# print("FINAL_LTP_ROWS =", len(final_ltp_df))
# print(final_ltp_df[["Strike", "Type", "LTP"]].head(20))

# Convert into option-chain format
ce_df = final_ltp_df[final_ltp_df["Type"] == "CE"].copy()
ce_df = ce_df[["Strike", "LTP", "OI", "Volume", "PriceChange", "PricePctChange"]]
ce_df.columns = ["Strike", "CE_LTP", "CE OI", "CE Volume", "CE Price Change", "CE Price % Change"]

pe_df = final_ltp_df[final_ltp_df["Type"] == "PE"].copy()
pe_df = pe_df[["Strike", "LTP", "OI", "Volume", "PriceChange", "PricePctChange"]]
pe_df.columns = ["Strike", "PE_LTP", "PE OI", "PE Volume", "PE Price Change", "PE Price % Change"]

# print("CE_ROWS =", len(ce_df))
# print("PE_ROWS =", len(pe_df))

option_chain = pd.merge(
    ce_df,
    pe_df,
    on="Strike"
)

# print(option_chain.columns.tolist())

T = get_time_to_expiry(selected_expiry)

sigma = 0.115

def add_greeks(row):
    K = float(row["Strike"])

    ce_delta, ce_gamma, ce_theta, ce_vega = calculate_greeks(
        spot, K, T=T, sigma=sigma, opt_type="CE"
    )

    pe_delta, pe_gamma, pe_theta, pe_vega = calculate_greeks(
        spot, K, T=T, sigma=sigma, opt_type="PE"
    )

    return pd.Series({
    "CE Delta": ce_delta,
    "CE Gamma": ce_gamma,
    "CE Theta": ce_theta,
    "CE Vega": ce_vega,

    "PE Delta": pe_delta,
    "PE Gamma": pe_gamma,
    "PE Theta": pe_theta,
    "PE Vega": pe_vega
    })

greeks_df = option_chain.apply(add_greeks, axis=1)
option_chain = pd.concat([option_chain, greeks_df], axis=1)

option_chain = option_chain.loc[:, ~option_chain.columns.duplicated()]
option_chain = option_chain.reset_index(drop=True)

# print("\nNIFTY OPTION CHAIN")
# # print("OPTION_CHAIN COLUMNS =")
# print(option_chain.columns.tolist())
# print(option_chain[[
#     "Strike",
#     "CE_LTP", "CE OI", "CE Volume", "CE Price Change", "CE Price % Change",
#     "PE_LTP", "PE OI", "PE Volume", "PE Price Change", "PE Price % Change"
# ]].to_string(index=False))

option_chain["Expiry"] = selected_expiry
option_chain["Spot"] = spot
# option_chain.to_csv("option_chain.csv", index=False)
# print("option_chain.csv saved")

# Step 4: ATM / ITM / OTM identification

# spot already defined above

# print("ROWS IN OPTION_CHAIN =", len(option_chain))
# print(option_chain.columns.tolist())

option_chain["Strike"] = pd.to_numeric(option_chain["Strike"], errors="coerce")
option_chain = option_chain.dropna(subset=["Strike"])
option_chain["Distance"] = abs(option_chain["Strike"] - spot)

atm_strike = round(spot / 50) * 50

option_chain["Status"] = option_chain["Strike"].apply(
    lambda x: "ATM" if x == atm_strike else
              "ITM CE / OTM PE" if x < spot else
              "OTM CE / ITM PE"
)

print("\nATM Strike =", atm_strike)
# print(option_df["Strike"].tolist())
# exit()

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

# # print("\nATM CE TOKEN")
# print(atm_ce[["pTrdSymbol", "pSymbol"]].to_string(index=False))

# # print("\nATM PE TOKEN")
# print(atm_pe[["pTrdSymbol", "pSymbol"]].to_string(index=False))
ce_token = str(atm_ce.iloc[0]["pSymbol"])
pe_token = str(atm_pe.iloc[0]["pSymbol"])

# print("\nCE TOKEN =", ce_token)
# print("PE TOKEN =", pe_token)

with open("tokens.txt", "w") as f:
    f.write(f"{ce_token}\n")
    f.write(f"{pe_token}\n")
    f.write(f"{atm_strike}\n") 
    f.write(f"{atm_strike}\n")

# print("Tokens saved to tokens.txt")

print("\nNIFTY OPTION CHAIN WITH STATUS")
print(option_chain.to_string(index=False))

option_chain.to_csv("dashboard_data.csv", index=False)
print("dashboard_data.csv updated")

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

            
    option_chain = option_chain.loc[:, ~option_chain.columns.duplicated()].copy()

# if "Trading_Bias" in option_chain.columns:
#     option_chain = option_chain.drop(columns=["Trading_Bias"])
   
#     option_chain["Trading_Bias"] = "Neutral" 

# option_chain["Trading_Bias"] = option_chain.apply(
#     trading_bias,
#     axis=1
# )
# print("\nTOP 3 CE SELL CANDIDATES")
# print(
#     option_chain[
#         option_chain["Trading_Bias"].str.contains("CE Sell", na=False)
#     ][["Strike", "CE_TimeValue", "Trading_Bias"]]
#     # .sort_values("CE_TimeValue", ascending=False)
#     .head(3)
#     .to_string(index=False)
# )

# print("\nTOP 3 PE SELL CANDIDATES")
# print(
#     option_chain[
#         option_chain["Trading_Bias"].str.contains("PE Sell", na=False)
#     ][["Strike", "PE_TimeValue", "Trading_Bias"]]
#     # .sort_values("PE_TimeValue", ascending=False)
#     .head(3)
#     .to_string(index=False)
# )
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
        ]]
    .to_string(index=False)
)