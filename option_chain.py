from datetime import datetime
import pandas as pd
from scipy.stats import norm
from math import log, sqrt, exp

def get_time_to_expiry(expiry):
    try:
        expiry_date = datetime.strptime(str(expiry), "%d%b%Y")
        today = datetime.now()
        days = max((expiry_date.date() - today.date()).days, 1)
        return days / 365
    except Exception as e:
        print("EXPIRY ERROR =", str(e))
        return 7 / 365
    
def calculate_greeks(S, K, T=7/365, r=0.06, sigma=0.164, opt_type="CE"):
    # print("CALCULATE_GREEKS CALLED")
    # print("S=", S)
    # print("K=", K)
    # print("T=", T)
    # print("sigma=", sigma)
    try:
        S = float(S)
        K = float(K)
        T = float(T)
        sigma = float(sigma)
        
        print("CHECK:", S, K, T, sigma)

        if S <= 0 or K <= 0 or T <= 0 or sigma <= 0:
            print("FAILED CHECK")
            return "NA", "NA", "NA", "NA"

        d1 = (log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * sqrt(T))
        d2 = d1 - sigma * sqrt(T)

        gamma = norm.pdf(d1) / (S * sigma * sqrt(T))
        vega = S * norm.pdf(d1) * sqrt(T) / 100

        if opt_type == "CE":
            delta = norm.cdf(d1)
            theta = (-(S * norm.pdf(d1) * sigma) / (2 * sqrt(T)) - r * K * exp(-r*T) * norm.cdf(d2)) / 365
        else:
            delta = norm.cdf(d1) - 1
            theta = (-(S * norm.pdf(d1) * sigma) / (2 * sqrt(T)) + r * K * exp(-r*T) * norm.cdf(-d2)) / 365

        return round(delta, 3), round(gamma, 5), round(theta, 2), round(vega, 2)

    except Exception as e:
        print("GREEK ERROR =", e)
        return "NA", "NA", "NA", "NA"

def calculate_pcr(option_chain_data, spot=None):
    rows = []

    for item in option_chain_data:
        expiry = item.get("expiryDate", "")
        strike = item.get("strikePrice")
        T = get_time_to_expiry(expiry)

        ce = item.get("CE", {})
        pe = item.get("PE", {})
        if spot is None:
            spot = strike

        ce_delta, ce_gamma, ce_theta, ce_vega = calculate_greeks(
            spot, strike, T=T, opt_type="CE"
        )

        pe_delta, pe_gamma, pe_theta, pe_vega = calculate_greeks(
            spot, strike, T=T, opt_type="PE"
        )
        
        ce_oi = ce.get("openInterest", 0) or 0
        pe_oi = pe.get("openInterest", 0) or 0
        if strike == 24100:
            print("\nCE KEYS:")
            print(ce.keys())

            print("\nPE KEYS:")
            print(pe.keys())

        print("CE IV CHECK =", {k: v for k, v in ce.items() if "iv" in k.lower() or "vol" in k.lower() or "sigma" in k.lower()})
        print("PE IV CHECK =", {k: v for k, v in pe.items() if "iv" in k.lower() or "vol" in k.lower() or "sigma" in k.lower()})
            
        ce_volume = ce.get("totalTradedVolume", 0) or 0
        pe_volume = pe.get("totalTradedVolume", 0) or 0
        print("STRIKE =", strike)
        print("CE VOL =", ce_volume)
        print("PE VOL =", pe_volume)

        if spot is None:
            spot = strike

        ce_delta, ce_gamma, ce_theta, ce_vega = calculate_greeks(
            spot, strike, opt_type="CE"
        )

        pe_delta, pe_gamma, pe_theta, pe_vega = calculate_greeks(
            spot, strike, opt_type="PE"
        )

        rows.append({
            "Expiry": expiry,
            "Strike": strike,

            "CE LTP": ce.get("lastPrice", 0),
            "CE OI": ce_oi,
            "CE Volume": ce_volume,
            "CE Delta": ce_delta,
            "CE Gamma": ce_gamma,
            "CE Theta": ce_theta,
            "CE Vega": ce_vega,

            "PE LTP": pe.get("lastPrice", 0),
            "PE OI": pe_oi,
            "PE Volume": pe_volume,
            "PE Delta": pe_delta,
            "PE Gamma": pe_gamma,
            "PE Theta": pe_theta,
            "PE Vega": pe_vega,

            "OI PCR": round(pe_oi / ce_oi, 2) if ce_oi > 0 else 0,
            "Volume PCR": round(pe_volume / ce_volume, 2) if ce_volume > 0 else 0
        })

    return pd.DataFrame(rows)


def expiry_summary(pcr_df):
    summary = pcr_df.groupby("Expiry").agg({
        "CE OI": "sum",
        "PE OI": "sum",
        "CE Volume": "sum",
        "PE Volume": "sum"
    }).reset_index()

    summary["OI PCR"] = summary.apply(
        lambda x: round(x["PE OI"] / x["CE OI"], 2) if x["CE OI"] > 0 else 0,
        axis=1
    )

    summary["Volume PCR"] = summary.apply(
        lambda x: round(x["PE Volume"] / x["CE Volume"], 2) if x["CE Volume"] > 0 else 0,
        axis=1
    )

    return summary