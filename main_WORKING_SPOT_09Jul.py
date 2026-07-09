from neo_api_client import NeoAPI
from dotenv import load_dotenv
import os
import time
from datetime import datetime, timedelta, timezone
from datetime import time as dt_time
from option_chain import (
    calculate_pcr,
    expiry_summary,
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
expiry_printed = False
table_printed = False

# ---------- 9:15 DAILY CSV RESET ----------
# from datetime import datetime, time
import os

csv_files_to_refresh = [
    "option_chain.csv",
    "option_chain_full.csv",
    "opening_oi_baseline.csv",
    "pcr_history.csv",
    "chart_history.csv",
]

marker = ".last_reset"

now = datetime.now()
today = now.strftime("%Y-%m-%d")

if now.time() >= dt_time(9, 15):
    last_reset = ""

    if os.path.exists(marker):
        with open(marker) as f:
            last_reset = f.read().strip()

    if today != last_reset:

        protected = {
            "option_chain_base_oi_opening.csv",
            "option_chain_base_oi_closing.csv"
        }

        for f in csv_files_to_refresh:
            if f not in protected and os.path.exists(f):
                os.remove(f)

        with open(marker, "w") as f:
            f.write(today)

        with open(marker, "w") as f:
            f.write(today)

        print("CSV files cleared after 9:15 for new trading day.")
# ------------------------------------------------

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

    if not os.path.exists("selected_expiry_runtime.txt"):

        print("\nAVAILABLE EXPIRIES")
        for i, e in enumerate(expiry_list, start=1):
            print(f"{i}. {e}")

        if os.path.exists("selected_expiry.txt") and os.environ.get("LAUNCHER_MODE") == "1":
            with open("selected_expiry.txt", "r") as f:
                expiry_choice = int(f.read().strip())
            print(f"Using Launcher Expiry : {expiry_choice}")
        else:
            expiry_choice = int(input("Select Expiry (1,2,3...): "))

        with open("selected_expiry_runtime.txt", "w") as f:
            f.write(str(expiry_choice))

    else:
        with open("selected_expiry_runtime.txt", "r") as f:
            expiry_choice = int(f.read().strip())
        print("Using same Expiry =", expiry_choice)

    selected_expiry = expiry_list[expiry_choice - 1]

    print("Selected Expiry =", selected_expiry)

    option_df = option_df[
    option_df["pExpiryDate"] == selected_expiry
    ]
    option_df = option_df[
    option_df["pTrdSymbol"].astype(str).str.endswith(("CE", "PE"))
    ].copy()
    
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
       
    try:
        with open("nifty_spot_live.txt", "r") as f:
            spot = float(f.read().strip())
        print("SPOT FILE VALUE USED =", spot)
    except Exception:
        spot = 0
    if spot <= 0:
        spot = float(option_df["Strike"].median())

    atm = round(spot / 50) * 50
    lower_strike = atm - 500
    upper_strike = atm + 500

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

        # if int(row["Strike"]) == 24400:
        #     print("\n===== RAW NEO OI DEBUG =====")
        #     print("Strike:", row.get("Strike"))
        #     print("Row columns:", list(row.index))
        #     print("Token:", token)
        #     print("open_int:", ltp_row.get("open_int"))
        #     print("oi:", ltp_row.get("oi"))
        #     print("OI:", ltp_row.get("OI"))
        #     print("volume:", ltp_row.get("last_volume"))
        #     print("all keys:", ltp_row.keys())
        #     print("============================")

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
    print("DEBUG final_ltp_df columns:", ltp_df.columns.tolist())
    print(ltp_df.head(3).to_string())  

    final_ltp_df = pd.DataFrame(ltp_rows)
    final_ltp_df = final_ltp_df[final_ltp_df["LTP"] > 0].copy()

    final_ltp_df = final_ltp_df.sort_values(["Strike", "Type", "LTP"], ascending=[True, True, False])
    final_ltp_df = final_ltp_df.drop_duplicates(subset=["Strike", "Type"], keep="last")

    
    # Convert into option-chain format
    ce_df = final_ltp_df[final_ltp_df["Type"] == "CE"].copy()
    ce_df = ce_df[["Strike", "LTP", "OI", "Volume", "PriceChange", "PricePctChange", "IV"]]
    ce_df.columns = ["Strike", "CE_LTP", "CE OI", "CE Volume", "CE Price Change", "CE Price % Change", "CE_IV"]

    pe_df = final_ltp_df[final_ltp_df["Type"] == "PE"].copy()
    pe_df = pe_df[["Strike", "LTP", "OI", "Volume", "PriceChange", "PricePctChange", "IV"]]
    pe_df.columns = ["Strike", "PE_LTP", "PE OI", "PE Volume", "PE Price Change", "PE Price % Change", "PE_IV"]

    option_chain = pd.merge(
        ce_df,
        pe_df,
        on="Strike"
    )
   
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
        "CE_IV": round(ce_sigma * 100, 2) if ce_sigma is not None else 0,
        "PE_IV": round(pe_sigma * 100, 2) if pe_sigma is not None else 0,
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

    # --------- STATIC OI BASELINE LOGIC ---------
    import os
    from datetime import datetime, timedelta

    closing_file = "option_chain_base_oi_closing.csv"
    opening_file = "option_chain_base_oi_opening.csv"

    now_ist = datetime.now(timezone.utc) + timedelta(hours=5, minutes=30)
    time_now = now_ist.strftime("%H:%M")
    date_now = now_ist.strftime("%Y-%m-%d")
    time_only = now_ist.strftime("%H:%M:%S")

    # ----------------------------------------------------
    # SAVE CLOSING OI AFTER MARKET CLOSE (ONLY ONCE PER DAY)
    # ----------------------------------------------------

    closing_marker = "option_chain_base_oi_closing_date.txt"

    last_closing_date = ""
    if os.path.exists(closing_marker):
        with open(closing_marker, "r") as f:
            last_closing_date = f.read().strip()

    if time_now >= "15:30" and last_closing_date != date_now:

        closing_df = option_chain[["Strike", "CE OI", "PE OI"]].copy()

        closing_df.insert(0, "Date", date_now)
        closing_df.insert(1, "Time", time_only)

        closing_df.columns = [
            "Date",
            "Time",
            "Strike",
            "CE OI Open",
            "PE OI Open"
        ]

        closing_df.to_csv(closing_file, index=False)

        with open(closing_marker, "w") as f:
            f.write(date_now)

        print(f"Closing OI baseline saved once : {date_now} {time_only}")

    # ----------------------------------------------------
    # READ STATIC OPENING BASELINE
    # (User manually copies Closing → Opening)
    # ----------------------------------------------------
    if not os.path.exists(opening_file):
        raise FileNotFoundError(
            "\nERROR:\n"
            "option_chain_base_oi_opening.csv not found.\n"
            "Copy option_chain_base_oi_closing.csv "
            "to option_chain_base_oi_opening.csv before market opens."
        )

    baseline_df = pd.read_csv(opening_file)

    baseline_df["Strike"] = pd.to_numeric(baseline_df["Strike"], errors="coerce")
    baseline_df["CE OI Open"] = pd.to_numeric(baseline_df["CE OI Open"], errors="coerce")
    baseline_df["PE OI Open"] = pd.to_numeric(baseline_df["PE OI Open"], errors="coerce")

    print("\nBASELINE FILE CHECK")
    print(baseline_df[baseline_df["Strike"].isin([24050,24100,24150,24200,24400])])

    option_chain = option_chain.drop(
        columns=["CE OI Open", "PE OI Open"],
        errors="ignore"
    )

    baseline_df = baseline_df[[
        "Strike",
        "CE OI Open",
        "PE OI Open"
    ]]

    option_chain = pd.merge(
        option_chain,
        baseline_df,
        on="Strike",
        how="left"
    )

    option_chain["CE OI Open"] = (
        pd.to_numeric(option_chain["CE OI Open"], errors="coerce")
        .fillna(option_chain["CE OI"])
    )

    option_chain["PE OI Open"] = (
        pd.to_numeric(option_chain["PE OI Open"], errors="coerce")
        .fillna(option_chain["PE OI"])
    )

    option_chain["CE OI"] = pd.to_numeric(option_chain["CE OI"], errors="coerce").fillna(0)
    option_chain["PE OI"] = pd.to_numeric(option_chain["PE OI"], errors="coerce").fillna(0)

    # ----------------------------------------------------
    # OI CHANGE
    # ----------------------------------------------------
    option_chain["CE OI Change"] = option_chain["CE OI"] - option_chain["CE OI Open"]
    option_chain["PE OI Change"] = option_chain["PE OI"] - option_chain["PE OI Open"]

    debug = option_chain[option_chain["Strike"].isin([24050,24100,24150,24200,24400])]

    print("\n===== OI CHANGE CHECK =====")
    print(
        debug[
            [
                "Strike",
                "CE OI",
                "CE OI Open",
                "CE OI Change",
                "PE OI",
                "PE OI Open",
                "PE OI Change",
            ]
        ].to_string(index=False)
    )
    print("===============================\n")
    
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
    
    def calculate_max_pain(df):
        strikes = sorted(df["Strike"].dropna().unique())
        pain_list = []

        for expiry_price in strikes:
            ce_pain = ((expiry_price - df["Strike"]).clip(lower=0) * df["CE OI"]).sum()

            pe_pain = ((df["Strike"] - expiry_price).clip(lower=0) * df["PE OI"]).sum()

            total_pain = ce_pain + pe_pain

            pain_list.append((expiry_price, total_pain))

            # print(f"{expiry_price:6.0f} | CE Pain={ce_pain:15.0f} | PE Pain={pe_pain:15.0f} | Total={total_pain:15.0f}")

            # pain_list.append((expiry_price, total_pain))

        pain_df = pd.DataFrame(pain_list, columns=["Strike", "Total Pain"])

        return pain_df.loc[pain_df["Total Pain"].idxmin(), "Strike"]
        
        
    # ---------- CHART HISTORY ----------
    from datetime import datetime

    history_file = "chart_history.csv"

    total_ce_oi = option_chain["CE OI"].sum()
    total_pe_oi = option_chain["PE OI"].sum()
    total_ce_vol = option_chain["CE Volume"].sum()
    total_pe_vol = option_chain["PE Volume"].sum()

    overall_oi_pcr = round(total_pe_oi / total_ce_oi, 2) if total_ce_oi != 0 else 0
    overall_vol_pcr = round(total_pe_vol / total_ce_vol, 2) if total_ce_vol != 0 else 0

    ce_open = option_chain["CE OI Open"].sum()
    pe_open = option_chain["PE OI Open"].sum()

    ce_now = option_chain["CE OI"].sum()
    pe_now = option_chain["PE OI"].sum()

    ce_change = ce_now - ce_open
    pe_change = pe_now - pe_open

    total_ce_oi_change = option_chain["CE OI Change"].sum()
    total_pe_oi_change = option_chain["PE OI Change"].sum()

    overall_oi_pcr_change = round(total_pe_oi_change / total_ce_oi_change, 2) if total_ce_oi_change != 0 else 0

    max_pain = calculate_max_pain(option_chain)
    check = option_chain[option_chain["Strike"].isin([24050, 24100, 24150, 24200, 24400])]

    print("\n===== OI CHECK =====")
    print(check[["Strike", "CE OI", "PE OI"]].to_string(index=False))
    print("====================\n")

    if max_pain == 0 or pd.isna(max_pain):
        if os.path.exists("chart_history.csv"):
            old_hist = pd.read_csv("chart_history.csv")
            if "Max Pain" in old_hist.columns and not old_hist.empty:
                last_valid = old_hist[old_hist["Max Pain"] > 0]["Max Pain"]
                max_pain = int(last_valid.iloc[-1]) if not last_valid.empty else 0
                
    print("Max Pain =", max_pain)

    # print("\n" + "="*70)
    # print("                 OI PCR CHANGE DEBUG")
    # print("="*70)

    # opening_ce_oi_total = option_chain["CE OI Open"].sum()
    # opening_pe_oi_total = option_chain["PE OI Open"].sum()
    # current_ce_oi_total = option_chain["CE OI"].sum()
    # current_pe_oi_total = option_chain["PE OI"].sum()

    # print(f"Opening Total CE OI : {opening_ce_oi_total:,.0f}")
    # print(f"Current Total CE OI : {current_ce_oi_total:,.0f}")
    # print(f"Total CE OI Change  : {total_ce_oi_change:+,.0f}")

    # print(f"Opening Total PE OI : {opening_pe_oi_total:,.0f}")
    # print(f"Current Total PE OI : {current_pe_oi_total:,.0f}")
    # print(f"Total PE OI Change  : {total_pe_oi_change:+,.0f}")

    # print(f"Overall OI PCR      : {overall_oi_pcr:.4f}")

    # if total_ce_oi_change != 0:
    #     calc_delta = total_pe_oi_change / total_ce_oi_change
    #     print(f"PE Change / CE Change = {total_pe_oi_change:,.0f} / {total_ce_oi_change:,.0f}")
    #     print(f"Calculated PCR Delta  = {calc_delta:.4f}")
    #     print(f"Dashboard PCR Delta   = {calc_delta:.4f}")
    # else:
    #     print("CE OI Change is ZERO - cannot divide.")

    # print("="*70 + "\n")

    history_row = pd.DataFrame([{
        "Date": (datetime.now(timezone.utc) + timedelta(hours=5, minutes=30)).strftime("%d-%b-%Y"),
        "Time": (datetime.now(timezone.utc) + timedelta(hours=5, minutes=30)).strftime("%H:%M:%S"),
        "Spot": spot,
        "OI PCR": overall_oi_pcr,
        "Vol PCR": overall_vol_pcr,
        "OI PCR Change": overall_oi_pcr_change,
        "CE OI Change": total_ce_oi_change,
        "PE OI Change": total_pe_oi_change,
        "Max Pain": int(max_pain),
    }])

    # print(history_row.to_string(index=False))

    if os.path.exists(history_file):
        try:
            old_history = pd.read_csv(history_file)
        except:
            old_history = pd.DataFrame()

        if old_history.empty:
            chart_history = history_row
        else:
            chart_history = pd.concat([old_history, history_row], ignore_index=True)
    else:
            chart_history = history_row

    chart_history = chart_history.tail(300)
    chart_history.to_csv(history_file, index=False)
    # print("CHART ROWS =", len(chart_history))
    
    option_chain["Strike"] = pd.to_numeric(option_chain["Strike"], errors="coerce")
    option_chain = option_chain.dropna(subset=["Strike"])
    option_chain["Distance"] = abs(option_chain["Strike"] - spot)

    atm_strike = round(spot / 50) * 50

    option_chain["Status"] = option_chain["Strike"].apply(
    lambda x: "ATM" if x == atm_strike else
    "ITM CE / OTM PE" if x < spot else
    "OTM CE / ITM PE"
    )

    option_chain_full = option_chain.copy()
    option_chain_full.to_csv("option_chain_full.csv", index=False)

    option_chain.to_csv("option_chain.csv", index=False)

    summary_df = expiry_summary(option_chain)
    summary_df.to_csv("summary.csv", index=False)
    print("summary.csv updated")

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
    "CE_IV", "PE_IV",
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
    import time as tm
    tm.sleep(5)