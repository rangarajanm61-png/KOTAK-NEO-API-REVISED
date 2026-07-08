from scipy.optimize import brentq
from datetime import datetime, timedelta, timezone
import pandas as pd
import math
print("USING OPTION_CHAIN.PY")
from scipy.stats import norm
from math import log, sqrt, exp

def get_time_to_expiry(expiry):
    try:
        expiry_date = datetime.strptime(str(expiry), "%d%b%Y")

        # NIFTY option expiry assumed 3:30 PM India time
        expiry_datetime = expiry_date.replace(hour=15, minute=30, second=0)

        now = (datetime.now(timezone.utc) + timedelta(hours=5, minutes=30)).replace(tzinfo=None)
        
        remaining_seconds = (expiry_datetime - now).total_seconds()

        # print("\n===== EXPIRY TIME DEBUG =====")
        # print("Now =", now.strftime("%d-%b-%Y %H:%M:%S"))
        # print("Expiry datetime =", expiry_datetime.strftime("%d-%b-%Y %H:%M:%S"))
        # print("Remaining hours =", round(remaining_seconds / 3600, 2))
        # print("Remaining days =", round(remaining_seconds / (24 * 3600), 4))
        # print("=============================\n")

        # minimum small positive time to avoid zero error
        remaining_seconds = max(remaining_seconds, 60)

        return remaining_seconds / (365 * 24 * 60 * 60)

    except Exception as e:
        print("EXPIRY ERROR =", str(e))
        return 1 / 365
    
def calculate_iv(spot, strike, T, option_price, opt_type="CE", r=0.0):
    if option_price <= 0 or spot <= 0 or strike <= 0 or T <= 0:
        return None

    def bs_price(sigma):
        d1 = (log(spot / strike) + (r + 0.5 * sigma ** 2) * T) / (sigma * sqrt(T))
        d2 = d1 - sigma * sqrt(T)

        if opt_type == "CE":
            return spot * norm.cdf(d1) - strike * exp(-r * T) * norm.cdf(d2)
        else:
            return strike * exp(-r * T) * norm.cdf(-d2) - spot * norm.cdf(-d1)

    try:
        iv = brentq(lambda sigma: bs_price(sigma) - option_price, 0.01, 3.00)
        return iv
    except:
        return None


def option_price_bs(S, K, T, sigma, opt_type="CE", r=0.0):
    d1 = (log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * sqrt(T))
    d2 = d1 - sigma * sqrt(T)

    if opt_type == "CE":
        return S * norm.cdf(d1) - K * exp(-r * T) * norm.cdf(d2)
    else:
        return K * exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)


def calculate_decay(S, K, T, sigma, current_price, opt_type="CE", r=0.06):
    now = (datetime.now(timezone.utc) + timedelta(hours=5, minutes=30)).replace(tzinfo=None)

    next_open = now.replace(hour=9, minute=30, second=0, microsecond=0)

    if now >= next_open:
        next_open = next_open + timedelta(days=1)

    hours_to_next_open = (next_open - now).total_seconds() / 3600
    dt = hours_to_next_open / (365 * 24)

    T_next = max(T - dt, 1 / (365 * 24 * 60))

    price_now = option_price_bs(S, K, T, sigma, opt_type, r)
    price_next = option_price_bs(S, K, T_next, sigma, opt_type, r)

    return round(price_next - price_now, 2)


def calculate_greeks(S, K, T=7/365, r=0.0, sigma=0.164, opt_type="CE"):
    try:
        S = float(S)
        K = float(K)
        T = float(T)
        sigma = float(sigma)

        if S <= 0 or K <= 0 or T <= 0 or sigma <= 0:
            return "NA", "NA", "NA", "NA"

        d1 = (log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * sqrt(T))
        d2 = d1 - sigma * sqrt(T)

        gamma = norm.pdf(d1) / (S * sigma * sqrt(T))
        vega = S * norm.pdf(d1) * sqrt(T) / 100

        if opt_type == "CE":
            delta = norm.cdf(d1)
            theta = (
                -(S * norm.pdf(d1) * sigma) / (2 * sqrt(T))
                - r * K * exp(-r * T) * norm.cdf(d2)
            ) / 365
        else:
            delta = norm.cdf(d1) - 1
            theta = (
                -(S * norm.pdf(d1) * sigma) / (2 * sqrt(T))
                + r * K * exp(-r * T) * norm.cdf(-d2)
            ) / 365

        return round(delta, 4), round(gamma, 6), round(theta, 2), round(vega, 4)

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

        ce_iv = ce.get("impliedVolatility") or ce.get("iv") or ce.get("IV") or ce.get("implied_volatility") or ce.get("volatility") or 16.4
        pe_iv = pe.get("impliedVolatility") or pe.get("iv") or pe.get("IV") or pe.get("implied_volatility") or pe.get("volatility") or 16.4

        if int(strike) in [22100, 22500, 23000, 23100]:
            print("STRIKE", strike, "CE_IV", ce_iv, "PE_IV", pe_iv)
            print("CE KEYS", ce.keys())
            print("PE KEYS", pe.keys())

        ce_sigma = float(ce_iv) / 100
        pe_sigma = float(pe_iv) / 100

        ce_delta, ce_gamma, ce_theta, ce_vega = calculate_greeks(
            spot, strike, T=T, sigma=ce_sigma, opt_type="CE"
        )

        pe_delta, pe_gamma, pe_theta, pe_vega = calculate_greeks(
            spot, strike, T=T, sigma=pe_sigma, opt_type="PE"
        )
        
        ce_oi = ce.get("openInterest", 0) or 0
        pe_oi = pe.get("openInterest", 0) or 0
        if strike == 24100:
            print("\nCE KEYS:")
            print(ce.keys())

            print("\nPE KEYS:")
            print(pe.keys())

        # print("CE IV CHECK =", {k: v for k, v in ce.items() if "iv" in k.lower() or "vol" in k.lower() or "sigma" in k.lower()})
        # print("PE IV CHECK =", {k: v for k, v in pe.items() if "iv" in k.lower() or "vol" in k.lower() or "sigma" in k.lower()})
            
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
        "PE Volume": "sum",
    }).reset_index()

    summary["OI PCR"] = summary.apply(
        lambda x: round(x["PE OI"] / x["CE OI"], 2) if x["CE OI"] > 0 else 0,
        axis=1
    )

    summary["Volume PCR"] = summary.apply(
        lambda x: round(x["PE Volume"] / x["CE Volume"], 2) if x["CE Volume"] > 0 else 0,
        axis=1
    )

    summary["PCR Change"] = pcr_df["OI PCR Change"].mean() if "OI PCR Change" in pcr_df.columns else 0

    summary.to_csv("summary.csv", index=False)

    return summary