from neo_api_client import NeoAPI
from dotenv import load_dotenv
import os
import time
from datetime import datetime, timedelta
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

expiry_printed = False
table_printed = False
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

    if not expiry_printed:
        print("AVAILABLE EXPIRIES:")
        for e in expiry_list:
            print(e)
        expiry_printed = True

    selected_expiry = "07Jul2026"
    print("Selected Expiry =", selected_expiry)

    option_df = option_df[
    option_df["pExpiryDate"] == selected_expiry
    ]

    option_df = option_df[
    option_df["pTrdSymbol"].astype(str).str.endswith(("CE", "PE"))
    ].copy()

    # print("OPTION ROWS AFTER EXPIRY FILTER =", len(option_df))
    # print(option_df[["Strike", "pOptionType", "pTrdSymbol", "pExpiryDate"]].head(20).to_string(index=False))

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

    # fut_df = fut_df[fut_df["pExpiryDate"] == selected_expiry]

    print("Selected Expiry =", selected_expiry)
    print("\nAVAILABLE NIFTY FUTURES:")
    print(fut_df[["pSymbol","pTrdSymbol","pExpiryDate"]].to_string(index=False))

    # Show serial numbers
    print("\nAVAILABLE NIFTY FUTURES:")
    for i, (_, row) in enumerate(fut_df.iterrows(), start=1):
        print(f"{i}. {row['pTrdSymbol']}   {row['pExpiryDate']}")

    choice = int(input("\nSelect Future (1,2,3...): "))

    selected_row = fut_df.iloc[choice - 1]
    fut_df = selected_row.to_frame().T

    print("Selected FUT =", selected_row["pTrdSymbol"])
    print("Selected FUT Expiry =", selected_row["pExpiryDate"])

    if not fut_df.empty:
        fut_token = str(fut_df.iloc[0]["pSymbol"])
    else:
        print("Selected FUT not found")
        fut_token = None

    if fut_token is not None:
        fut_quote = client.quotes(
            instrument_tokens=[{
                "exchange_segment": "nse_fo",
                "instrument_token": fut_token
            }],
            quote_type="all"
    )

        auto_fut_price = float(fut_quote[0].get("ltp", 0))
    else:
        auto_fut_price = 0

    if auto_fut_price > 0:
        spot = auto_fut_price

        print("AUTO FUT USED AS SPOT =", spot)
    else:
        spot = float(input("Enter Spot manually: "))
        print("MANUAL USED AS SPOT =", spot)

    # -------- END AUTO NIFTY FUT PROXY --------

    atm = round(spot / 50) * 50
    lower_strike = atm - 1000
    upper_strike = atm + 1000

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

            # TEMP IV DEBUG
            "IV": ltp_row.get("iv", ltp_row.get("IV", ltp_row.get("implied_volatility", 0))),
        })
    else:
        pass
        
    final_ltp_df = pd.DataFrame(ltp_rows)
    final_ltp_df = final_ltp_df[final_ltp_df["LTP"] > 0].copy()

    final_ltp_df = final_ltp_df.sort_values(["Strike", "Type", "LTP"], ascending=[True, True, False])
    final_ltp_df = final_ltp_df.drop_duplicates(subset=["Strike", "Type"], keep="last")

    
    # Convert into option-chain format
    ce_df = final_ltp_df[final_ltp_df["Type"] == "CE"].copy()
    ce_df = ce_df[["Strike", "LTP", "OI", "Volume", "PriceChange", "PricePctChange", "IV"]]
    ce_df.columns = ["Strike", "CE_LTP", "CE OI", "CE Volume", "CE Price Change", "CE Price % Change", "CE IV"]

    pe_df = final_ltp_df[final_ltp_df["Type"] == "PE"].copy()
    pe_df = pe_df[["Strike", "LTP", "OI", "Volume", "PriceChange", "PricePctChange", "IV"]]
    pe_df.columns = ["Strike", "PE_LTP", "PE OI", "PE Volume", "PE Price Change", "PE Price % Change", "PE IV"]

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

    # Temporary - next we'll freeze this like Sensibull
    T_theta = T

    def add_greeks(row):
        K = float(row["Strike"])
              
        ce_sigma = calculate_iv(spot, K, T, float(row["CE_LTP"]), "CE")
        pe_sigma = calculate_iv(spot, K, T, float(row["PE_LTP"]), "PE")

        if ce_sigma is not None and pe_sigma is not None:
                if abs(K - spot) <= 100:
                    sigma = pe_sigma
                else:
                    sigma = (ce_sigma + pe_sigma) / 2
        elif ce_sigma is not None:
            sigma = ce_sigma
        elif pe_sigma is not None:
            sigma = pe_sigma
        else:
            sigma = 0.18

        ce_sigma = sigma
        pe_sigma = sigma

        # For deep ITM CE, CE IV is unstable.
        # Use same strike PE IV because CE and PE should have similar IV.
        if float(row["CE_LTP"]) > 500 and float(row["PE_LTP"]) < 10:
            ce_sigma = pe_sigma
       
        if ce_sigma is None:
            ce_sigma = 0.18

        if pe_sigma is None:
            pe_sigma = 0.18

        
        ce_delta, ce_gamma, ce_theta, ce_vega = calculate_greeks(
            spot, K, T=T_theta, sigma=ce_sigma, opt_type="CE"
        )

        pe_delta, pe_gamma, pe_theta, pe_vega = calculate_greeks(
            spot, K, T=T_theta, sigma=pe_sigma, opt_type="PE"
        )
        ce_decay = calculate_decay(spot, K, T, ce_sigma, float(row["CE_LTP"]), "CE")
        pe_decay = calculate_decay(spot, K, T, pe_sigma, float(row["PE_LTP"]), "PE")
        
        return pd.Series({
        "CE IV": round(ce_sigma * 100, 2) if ce_sigma is not None else 0,
        "PE IV": round(pe_sigma * 100, 2) if pe_sigma is not None else 0,
        "CE Delta": ce_delta,
        "CE Gamma": ce_gamma,
        "CE Theta": ce_theta,
        "CE Decay": ce_decay,
        "CE Vega": ce_vega,

        "PE Delta": pe_delta,
        "PE Gamma": pe_gamma,
        "PE Theta": pe_theta,
        "PE Decay": pe_decay,
        "PE Vega": pe_vega,
        })
    option_chain = option_chain.sort_values("Strike").reset_index(drop=True)

    # option_chain["CE IV Smooth"] = option_chain["CE IV"].rolling(window=3, center=True, min_periods=1).mean()
    # option_chain["PE IV Smooth"] = option_chain["PE IV"].rolling(window=3, center=True, min_periods=1).mean()
    # option_chain = option_chain.sort_values("Strike").reset_index(drop=True)

    # option_chain["CE IV Raw"] = option_chain.apply(
    #     lambda row: calculate_iv(spot, float(row["Strike"]), T, float(row["CE_LTP"]), "CE") or 0,
    #     axis=1
    # )

    # option_chain["PE IV Raw"] = option_chain.apply(
    #     lambda row: calculate_iv(spot, float(row["Strike"]), T, float(row["PE_LTP"]), "PE") or 0,
    #     axis=1
    # )

    # option_chain["CE IV Smooth"] = option_chain["CE IV Raw"].rolling(
    #     window=3, center=True, min_periods=1
    # ).mean() * 100

    # option_chain["PE IV Smooth"] = option_chain["PE IV Raw"].rolling(
    #     window=3, center=True, min_periods=1
    # ).mean() * 100

    greeks_df = option_chain.apply(add_greeks, axis=1)
    option_chain = pd.concat([option_chain, greeks_df], axis=1)

    option_chain = option_chain.loc[:, ~option_chain.columns.duplicated(keep="last")]
    
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
        "Time": (datetime.utcnow() + timedelta(hours=5, minutes=30)).strftime("%H:%M:%S"),
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
    table2_cols = [
    "Strike",
    "CE_LTP", "PE_LTP", "Spot",
    "CE IV", "PE IV",
    "CE Delta", "CE Gamma", "CE Theta", "CE Decay", "CE Vega",
    "PE Delta", "PE Gamma", "PE Theta", "PE Decay", "PE Vega",
]
    table3_cols = [
    "Strike",
    "CE_LTP",
    "PE_LTP",
    "Status",
    "CE_TimeValue",
    "PE_TimeValue",
]
    table1_cols = [c for c in table1_cols if c in option_chain.columns]
    table2_cols = [c for c in table2_cols if c in option_chain.columns]
    table3_cols = [c for c in table3_cols if c in option_chain.columns]
    
# ==================== PRINT TABLES ====================
    if not table_printed:
            print("\nTABLE 1 - PRICE / OI / PCR")
            print(option_chain[table1_cols].to_string(index=False))

            print("\nTABLE 2 - OPTION CHAIN WITH GREEKS")
            print(option_chain[table2_cols].to_string(index=False))
            print("\nTheta Basis: Black-Scholes one-calendar-day theta calculated from live Spot, Strike, IV and remaining time to expiry.")
            print("Current code recalculates theta every refresh because remaining time T is changing even after market closed.")
            print("Decay Basis: Estimated premium erosion from current time based on the project decay logic, assuming Spot and IV remain unchanged.")
            print("Current code recalculates decay every refresh; after-market broker-style theta freeze is not yet implemented.\n")

            print("\nTABLE 3 - OPTION CHAIN WITH TRADING BIAS")
            print(option_chain[table3_cols].to_string(index=False))

            table_printed = True

    else:
            print(f"Refresh OK | Spot = {spot:.2f}")

        # Save latest data every refresh
    option_chain.to_csv("option_chain.csv", index=False)

        # ================= END MAIN OUTPUT TABLES =================

    print("Waiting 5 seconds...")
    time.sleep(5)