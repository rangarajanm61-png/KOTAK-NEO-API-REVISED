from neo_api_client import NeoAPI
from dotenv import load_dotenv
import os
import time
from datetime import datetime
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
print("--------------------------------\n")

first_print = True
while True:

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
    
    cols = ['pSymbolName', 'pTrdSymbol', 'pSymbol', 'pExchSeg']

    available_cols = [c for c in cols if c in df.columns]

    
    option = client.search_scrip(
        exchange_segment="nse_fo",
        symbol="NIFTY"
    )

    option_df = pd.DataFrame(option)
    
    option_df = option_df[option_df["pSymbolName"] == "NIFTY"]

    
    option_df = option_df[option_df["pInstName"] == "OPTIDX"]

    
    expiry_list = sorted(option_df["pExpiryDate"].dropna().unique())

    selected_expiry = "30Jun2026"
    print("Selected Expiry =", selected_expiry)

    option_df = option_df[
    option_df["pExpiryDate"] == selected_expiry
    ]

    option_df = option_df[
    option_df["pTrdSymbol"].astype(str).str.endswith(("CE", "PE"))
    ].copy()
    

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

    # Find 24000 CE for selected expiry
    sample_option = option_df[
        (option_df["Strike"] == 24000) &
        (option_df["pOptionType"] == "CE") &
        (option_df["pExpiryDate"] == selected_expiry)
    ]

    # -------- AUTO NIFTY FUT PROXY --------

    all_df = pd.DataFrame(option)

    fut_df = all_df[
        (all_df["pSymbolName"] == "NIFTY") &
        (all_df["pInstName"].astype(str).str.contains("FUT", na=False))
    ].copy()

    fut_df = fut_df[fut_df["pExpiryDate"] == selected_expiry]

    fut_token = str(fut_df.iloc[0]["pSymbol"])

    fut_quote = client.quotes(
        instrument_tokens=[{
            "exchange_segment": "nse_fo",
            "instrument_token": fut_token
        }],
        quote_type="all"
    )

    auto_fut_price = float(fut_quote[0].get("ltp", 0))
    spot = auto_fut_price

    print("AUTO FUT USED AS SPOT =", spot)

    # -------- END AUTO NIFTY FUT PROXY --------

    atm = round(spot / 50) * 50
    lower_strike = atm - 2000
    upper_strike = atm + 2000

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
            quote_type="all"
        )
        
        if isinstance(ltp_data, list) and len(ltp_data) > 0:
            ltp_row = ltp_data[0]

        ltp_rows.append({
            "Strike": int(row["Strike"]),
            "Type": row["pOptionType"],
            "LTP": float(ltp_row.get("ltp", 0) or 0),
            "PriceChange": float(ltp_row.get("change", 0) or 0),
            "PricePctChange": float(ltp_row.get("per_change", 0) or 0),
            "OI": int(ltp_row.get("open_int", 0) or 0),
            "Volume": int(ltp_row.get("last_volume", 0) or 0),
        })
    else:
        pass
        
    final_ltp_df = pd.DataFrame(ltp_rows)
    final_ltp_df = final_ltp_df[final_ltp_df["LTP"] > 0].copy()

    final_ltp_df = final_ltp_df.sort_values(["Strike", "Type", "LTP"], ascending=[True, True, False])
    final_ltp_df = final_ltp_df.drop_duplicates(subset=["Strike", "Type"], keep="last")

    
    # Convert into option-chain format
    ce_df = final_ltp_df[final_ltp_df["Type"] == "CE"].copy()
    ce_df = ce_df[["Strike", "LTP", "OI", "Volume", "PriceChange", "PricePctChange"]]
    ce_df.columns = ["Strike", "CE_LTP", "CE OI", "CE Volume", "CE Price Change", "CE Price % Change"]

    pe_df = final_ltp_df[final_ltp_df["Type"] == "PE"].copy()
    pe_df = pe_df[["Strike", "LTP", "OI", "Volume", "PriceChange", "PricePctChange"]]
    pe_df.columns = ["Strike", "PE_LTP", "PE OI", "PE Volume", "PE Price Change", "PE Price % Change"]

    option_chain = pd.merge(
        ce_df,
        pe_df,
        on="Strike"
    )
    # print("\n===== ALL AVAILABLE COLUMNS =====")
    # print(final_ltp_df.columns.tolist())

    # print("\n===== SAMPLE RECORD =====")
    # print(final_ltp_df.iloc[0].to_dict())

    # print("\n===== CE DATA COLUMNS =====")
    # print(ce_df.columns.tolist())

    # print("\n===== PE DATA COLUMNS =====")
    # print(pe_df.columns.tolist())

    # print("\n===== SAMPLE CE ROW =====")
    # print(ce_df.iloc[0].to_dict())

    # print("\n===== SAMPLE PE ROW =====")
    # print(pe_df.iloc[0].to_dict())

    T = get_time_to_expiry(selected_expiry)

    sigma = 0.108

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

    option_chain["Expiry"] = selected_expiry
    option_chain["Spot"] = spot
    # ---------- Dashboard Table 1 Columns ----------

    option_chain["OI PCR"] = option_chain.apply(
        lambda r: round(r["PE OI"] / r["CE OI"], 2)
        if r["CE OI"] != 0 else 0,
        axis=1
    )

    option_chain["PE/CE Vol Ratio"] = option_chain.apply(
        lambda r: round(r["PE Volume"] / r["CE Volume"], 2)
        if r["CE Volume"] != 0 else 0,
        axis=1
    )

    # ---------- OPENING OI BASELINE ----------
    baseline_file = "opening_oi_baseline.csv"

    # First time of the day: save opening OI as baseline
    if not os.path.exists(baseline_file):
        baseline_df = option_chain[["Strike", "CE OI", "PE OI"]].copy()
        baseline_df.columns = ["Strike", "CE OI Open", "PE OI Open"]
        baseline_df.to_csv(baseline_file, index=False)
        print("Opening OI baseline saved.")

    # Read baseline
    baseline_df = pd.read_csv(baseline_file)

    # Merge baseline with current option chain
    option_chain = pd.merge(
        option_chain,
        baseline_df,
        on="Strike",
        how="left"
    )
    # Fill missing OI Open values
    option_chain["CE OI Open"] = option_chain["CE OI Open"].fillna(option_chain["CE OI"])
    option_chain["PE OI Open"] = option_chain["PE OI Open"].fillna(option_chain["PE OI"])

    for col in ["CE OI", "PE OI", "CE OI Open", "PE OI Open"]:
        option_chain[col] = pd.to_numeric(option_chain[col], errors="coerce").fillna(0)

    # Calculate OI Change
    option_chain["CE OI Change"] = option_chain["CE OI"] - option_chain["CE OI Open"]
    option_chain["PE OI Change"] = option_chain["PE OI"] - option_chain["PE OI Open"]

    # Calculate OI Change %
    option_chain["CE OI Change %"] = option_chain.apply(
        lambda r: round((r["CE OI Change"] / r["CE OI Open"]) * 100, 2)
        if r["CE OI Open"] != 0 else 0,
        axis=1
    )

    option_chain["PE OI Change %"] = option_chain.apply(
        lambda r: round((r["PE OI Change"] / r["PE OI Open"]) * 100, 2)
        if r["PE OI Open"] != 0 else 0,
        axis=1
    )

    # Change OI PCR
    option_chain["OI PCR Change"] = option_chain.apply(
        lambda r: round(r["PE OI Change"] / r["CE OI Change"], 2)
        if r["CE OI Change"] != 0 else 0,
        axis=1
    )
    # ---------- CHART HISTORY ----------
    from datetime import datetime

    history_file = "chart_history.csv"

    total_ce_oi = option_chain["CE OI"].sum()
    total_pe_oi = option_chain["PE OI"].sum()
    total_ce_vol = option_chain["CE Volume"].sum()
    total_pe_vol = option_chain["PE Volume"].sum()

    overall_oi_pcr = round(total_pe_oi / total_ce_oi, 2) if total_ce_oi != 0 else 0
    overall_vol_pcr = round(total_pe_vol / total_ce_vol, 2) if total_ce_vol != 0 else 0

    total_ce_oi_change = option_chain["CE OI Change"].sum()
    total_pe_oi_change = option_chain["PE OI Change"].sum()

    overall_oi_pcr_change = (
        round(total_pe_oi_change / total_ce_oi_change, 2)
        if total_ce_oi_change != 0 else 0
    )

    history_row = pd.DataFrame([{
        "Time": datetime.now().strftime("%H:%M:%S"),
        "Spot": spot,
        "OI PCR": overall_oi_pcr,
        "Vol PCR": overall_vol_pcr,
        "OI PCR Change": overall_oi_pcr_change,
        "CE OI Change": total_ce_oi_change,
        "PE OI Change": total_pe_oi_change,
        "Max Pain": 0,
    }])

    if os.path.exists(history_file):
        old_history = pd.read_csv(history_file)
        chart_history = pd.concat([old_history, history_row], ignore_index=True)
    else:
        chart_history = history_row

    chart_history = chart_history.tail(300)
    chart_history.to_csv(history_file, index=False)

    option_chain["Strike"] = pd.to_numeric(option_chain["Strike"], errors="coerce")
    option_chain = option_chain.dropna(subset=["Strike"])
    option_chain["Distance"] = abs(option_chain["Strike"] - spot)

    atm_strike = round(spot / 50) * 50

    option_chain["Status"] = option_chain["Strike"].apply(
        lambda x: "ATM" if x == atm_strike else
                "ITM CE / OTM PE" if x < spot else
                "OTM CE / ITM PE"
    )
    option_chain.to_csv("option_chain.csv", index=False)

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

    ce_token = str(atm_ce.iloc[0]["pSymbol"])
    pe_token = str(atm_pe.iloc[0]["pSymbol"])

    with open("tokens.txt", "w") as f:
        f.write(f"{ce_token}\n")
        f.write(f"{pe_token}\n")
        f.write(f"{atm_strike}\n") 
        f.write(f"{atm_strike}\n")

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
    # ================= MAIN OUTPUT TABLES =================

    # ---- Table 1: Price / OI / PCR ----
    table1_cols = [
    "Strike",
    "CE_LTP",
    "CE OI",
    "CE OI Change",
    "CE OI Change %",
    "CE Volume",
    "CE Price Change",
    "PE_LTP",
    "PE OI",
    "PE OI Change",
    "PE OI Change %",
    "PE Volume",
    "PE Price Change",
    "OI PCR",
    "OI PCR Change",
    "PE/CE Vol Ratio",
    "Expiry",
    "Spot",
]
    table1_cols = [c for c in table1_cols if c in option_chain.columns]

    if first_print:
        print("\nTABLE 1 - PRICE / OI / PCR")
        print(option_chain[table1_cols].to_string(index=False))

        # ---- Table 2: Option Chain with Greeks ----
        table2_cols = [
            "Strike",
            "CE_LTP", "PE_LTP", "Spot",
            "CE Delta", "CE Gamma", "CE Theta", "CE Vega",
            "PE Delta", "PE Gamma", "PE Theta", "PE Vega"
        ]
        table2_cols = [c for c in table2_cols if c in option_chain.columns]

        print("\nTABLE 2 - OPTION CHAIN WITH GREEKS")
        print(option_chain[table2_cols].to_string(index=False))


        # ---- Table 3: Trading Bias ----
        table3_cols = [
            "Strike", "CE_LTP", "PE_LTP", "Status", "CE_TimeValue", "PE_TimeValue"
        ]
        table3_cols = [c for c in table3_cols if c in option_chain.columns]

        print("\nTABLE 3 - OPTION CHAIN WITH TRADING BIAS")
        print(option_chain[table3_cols].to_string(index=False))

        first_print = False
    else:
        print(f"Refresh OK | Spot = {spot:.2f}")

    # ================= END MAIN OUTPUT TABLES =================
    print("Waiting 5 seconds...")
    time.sleep(5)