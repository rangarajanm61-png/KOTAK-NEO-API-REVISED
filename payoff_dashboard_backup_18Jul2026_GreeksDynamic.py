from streamlit_autorefresh import st_autorefresh
from st_aggrid import AgGrid, GridOptionsBuilder
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import plotly.express as px
# import time
# from option_chain import calculate_pcr, expiry_summary
from datetime import datetime,date,time
from zoneinfo import ZoneInfo
import math
from scipy.stats import norm

IST = ZoneInfo("Asia/Kolkata")

st.set_page_config(layout="wide")
st.markdown("""
<style>

/* Extra compact payoff rows */
div[data-testid="stHorizontalBlock"] {
    gap: 0.20rem !important;
}

div[data-testid="stSelectbox"] {
    margin-bottom: 0 !important;
}

div[data-testid="stNumberInput"] {
    margin-bottom: 0 !important;
}

div[data-testid="stCheckbox"] {
    padding-top: 6px !important;
    margin-bottom: 0 !important;
}

div[data-testid="stElementContainer"] {
    margin-bottom: 0 !important;
}

h2 {
    font-size: 22px !important;
}

</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>

# /* Reduce page margins */

.block-container {
    padding-top: 0rem !important;
    padding-bottom: 0.2rem !important;
    padding-left: 1rem !important;
    padding-right: 1rem !important;
}

section.main > div {
    padding-top: 0rem !important;
}
div[data-testid="stVerticalBlock"] {
    gap: 0.35rem !important;
}
</style>
""", unsafe_allow_html=True)


# Read latest data separately for Table 3
try:
    option_df = pd.read_csv("option_chain.csv")

    option_df.columns = option_df.columns.str.strip()

    option_df.rename(
        columns={
            "CE_LTP": "CE LTP",
            "PE_LTP": "PE LTP"
        },
        inplace=True
    )

    option_df["Strike"] = pd.to_numeric(
        option_df["Strike"], errors="coerce"
    )

    option_df["CE LTP"] = pd.to_numeric(
        option_df["CE LTP"], errors="coerce"
    ).fillna(0)

    option_df["PE LTP"] = pd.to_numeric(
        option_df["PE LTP"], errors="coerce"
    ).fillna(0)

    option_df = option_df.dropna(subset=["Strike"])
    option_df["Strike"] = option_df["Strike"].astype(int)

except Exception as e:
    st.error(f"Table 3 data error: {e}")
    st.stop()
# =========================
# TABLE 3 - PAYOFF CALCULATOR
# =========================

LOT_SIZE = 65

def get_ltp_for_leg(df, strike, cepe):
    row = df[df["Strike"] == strike]
    if row.empty:
        return 0.0
    col = "CE LTP" if cepe == "CE" else "PE LTP"
    return float(row.iloc[0][col])

# Read current spot
try:
    with open("nifty_spot_live.txt", "r") as f:
        spot_now = float(f.read().strip())
except:
    if "Spot" in option_df.columns:
        spot_now = float(option_df["Spot"].iloc[0])
    else:
        spot_now = float(option_df["Strike"].median())

atm = round(spot_now / 50) * 50

now = datetime.now(IST)

title_col, time_col = st.columns([2.6, 2.4])

with title_col:
    st.markdown(
        "<h2 style='margin:0 0 8px 0; padding:0;'>"
        "Table 3 - Payoff Calculator"
        "</h2>",
        unsafe_allow_html=True
    )

with time_col:
    st.markdown(
        f"""
        <div style="
            text-align:right;
            padding-top:0px;
            padding-bottom:8px;
            font-size:13px;
            white-space:nowrap;
        ">
            Last Refresh : {now.strftime('%d-%b %H:%M:%S IST')}
        </div>
        """,
        unsafe_allow_html=True
    )
spot_col, atm_col, refresh_col = st.columns([2, 1.3, 1])

with spot_col:
    st.markdown(
        f"""
        <div style="font-size:15px; padding-top:7px; white-space:nowrap;">
            <b>Current Spot:</b>&nbsp;&nbsp;
            <span style="font-size:18px; font-weight:700;">
                ₹{spot_now:,.2f}
            </span>
        </div>
        """,
        unsafe_allow_html=True
    )

with atm_col:
    st.markdown(
        f"""
        <div style="font-size:15px; padding-top:7px; white-space:nowrap;">
            <b>ATM:</b>&nbsp;&nbsp;
            <span style="font-size:18px; font-weight:700;">
                {atm}
            </span>
        </div>
        """,
        unsafe_allow_html=True
    )

with refresh_col:
    if st.button(
        "Refresh LTP",
        key="refresh_payoff_data",
        use_container_width=True
    ):
        st.rerun()

strike_list = sorted(option_df["Strike"].unique())
near_strikes = [s for s in strike_list if atm - 500 <= s <= atm + 500]

def strike_label(s, cepe, atm):
    if s == atm:
        return f"{s}  ATM"
    if cepe == "CE":
        return f"{s}  {'ITM' if s < atm else 'OTM'}"
    else:
        return f"{s}  {'ITM' if s > atm else 'OTM'}"

def bs_option_price(spot, strike, time_years, iv, option_type, rate=0.065):
    """
    Black-Scholes theoretical option price.

    spot        : Scenario NIFTY spot
    strike      : Option strike
    time_years  : Remaining time in years
    iv          : Volatility as decimal, e.g. 0.12 for 12%
    option_type : "CE" or "PE"
    """

    try:
        spot = float(spot)
        strike = float(strike)
        time_years = max(float(time_years), 1e-8)
        iv = max(float(iv), 0.0001)

        d1 = (
            math.log(spot / strike)
            + (rate + 0.5 * iv**2) * time_years
        ) / (iv * math.sqrt(time_years))

        d2 = d1 - iv * math.sqrt(time_years)

        if option_type == "CE":
            return (
                spot * norm.cdf(d1)
                - strike * math.exp(-rate * time_years) * norm.cdf(d2)
            )

        return (
            strike * math.exp(-rate * time_years) * norm.cdf(-d2)
            - spot * norm.cdf(-d1)
        )

    except Exception:
        return 0.0       

def bs_greeks(
    spot,
    strike,
    time_years,
    iv,
    option_type,
    rate=0.065
):
    """
    Black-Scholes scenario Greeks.

    Returns:
        delta : option delta
        gamma : option gamma
        theta : one-calendar-day theta
        vega  : price change for 1 percentage-point IV change
    """

    try:
        spot = float(spot)
        strike = float(strike)
        time_years = max(float(time_years), 1e-8)
        iv = max(float(iv), 0.0001)

        sqrt_t = math.sqrt(time_years)

        d1 = (
            math.log(spot / strike)
            + (rate + 0.5 * iv**2) * time_years
        ) / (iv * sqrt_t)

        d2 = d1 - iv * sqrt_t

        pdf_d1 = norm.pdf(d1)

        gamma = pdf_d1 / (
            spot * iv * sqrt_t
        )

        vega = (
            spot * pdf_d1 * sqrt_t
        ) / 100.0

        if option_type == "CE":
            delta = norm.cdf(d1)

            theta_annual = (
                -(spot * pdf_d1 * iv) / (2.0 * sqrt_t)
                - rate
                * strike
                * math.exp(-rate * time_years)
                * norm.cdf(d2)
            )

        else:
            delta = norm.cdf(d1) - 1.0

            theta_annual = (
                -(spot * pdf_d1 * iv) / (2.0 * sqrt_t)
                + rate
                * strike
                * math.exp(-rate * time_years)
                * norm.cdf(-d2)
            )

        theta_daily = theta_annual / 365.0

        return {
            "delta": delta,
            "gamma": gamma,
            "theta": theta_daily,
            "vega": vega
        }

    except Exception:
        return {
            "delta": 0.0,
            "gamma": 0.0,
            "theta": 0.0,
            "vega": 0.0
        }         
# =========================================================
# STRATEGY LIBRARY
# =========================================================

strategy_options = [
    "Custom",
    "Long Call",
    "Long Put",
    "Bull Call Spread",
    "Bear Put Spread",
    "Bull Put Spread",
    "Bear Call Spread",
    "Long Straddle",
    "Short Straddle",
    "Long Strangle",
    "Short Strangle",
    "Iron Condor",
    "Iron Fly"
]

strategy_name = st.selectbox(
    "Select Strategy",
    strategy_options,
    index=0,
    key="strategy_name"
)

strategy_map = {
    "Custom": [],

    "Long Call": [
        {"buy_sell": "BUY", "cepe": "CE", "offset": 0, "lots": 1}
    ],

    "Long Put": [
        {"buy_sell": "BUY", "cepe": "PE", "offset": 0, "lots": 1}
    ],

    "Bull Call Spread": [
        {"buy_sell": "BUY",  "cepe": "CE", "offset": 0,   "lots": 1},
        {"buy_sell": "SELL", "cepe": "CE", "offset": 100, "lots": 1}
    ],

    "Bear Put Spread": [
        {"buy_sell": "BUY",  "cepe": "PE", "offset": 0,    "lots": 1},
        {"buy_sell": "SELL", "cepe": "PE", "offset": -100, "lots": 1}
    ],

    "Bull Put Spread": [
        {"buy_sell": "SELL", "cepe": "PE", "offset": 0,    "lots": 1},
        {"buy_sell": "BUY",  "cepe": "PE", "offset": -100, "lots": 1}
    ],

    "Bear Call Spread": [
        {"buy_sell": "SELL", "cepe": "CE", "offset": 0,   "lots": 1},
        {"buy_sell": "BUY",  "cepe": "CE", "offset": 100, "lots": 1}
    ],

    "Long Straddle": [
        {"buy_sell": "BUY", "cepe": "CE", "offset": 0, "lots": 1},
        {"buy_sell": "BUY", "cepe": "PE", "offset": 0, "lots": 1}
    ],

    "Short Straddle": [
        {"buy_sell": "SELL", "cepe": "CE", "offset": 0, "lots": 1},
        {"buy_sell": "SELL", "cepe": "PE", "offset": 0, "lots": 1}
    ],

    "Long Strangle": [
        {"buy_sell": "BUY", "cepe": "CE", "offset": 100,  "lots": 1},
        {"buy_sell": "BUY", "cepe": "PE", "offset": -100, "lots": 1}
    ],

    "Short Strangle": [
        {"buy_sell": "SELL", "cepe": "CE", "offset": 100,  "lots": 1},
        {"buy_sell": "SELL", "cepe": "PE", "offset": -100, "lots": 1}
    ],

    "Iron Condor": [
        {"buy_sell": "BUY",  "cepe": "PE", "offset": -200, "lots": 1},
        {"buy_sell": "SELL", "cepe": "PE", "offset": -100, "lots": 1},
        {"buy_sell": "SELL", "cepe": "CE", "offset": 100,  "lots": 1},
        {"buy_sell": "BUY",  "cepe": "CE", "offset": 200,  "lots": 1}
    ],

    "Iron Fly": [
        {"buy_sell": "BUY",  "cepe": "PE", "offset": -100, "lots": 1},
        {"buy_sell": "SELL", "cepe": "PE", "offset": 0,    "lots": 1},
        {"buy_sell": "SELL", "cepe": "CE", "offset": 0,    "lots": 1},
        {"buy_sell": "BUY",  "cepe": "CE", "offset": 100,  "lots": 1}
    ]
}

selected_template = strategy_map[strategy_name]
# ==========================================================
# SCENARIO DATE / TIME / IV CONTROLS
# ==========================================================

IST = ZoneInfo("Asia/Kolkata")

# Read selected expiry from option-chain data first
expiry_text = ""

if "Expiry" in option_df.columns:
    expiry_values = option_df["Expiry"].dropna().astype(str)

    if not expiry_values.empty:
        expiry_text = expiry_values.iloc[0].strip()

# Fallback to launcher expiry file
if not expiry_text:
    try:
        with open("selected_expiry.txt", "r") as f:
            expiry_text = f.read().strip()
    except Exception:
        expiry_text = ""

# Convert expiry such as 21Jul2026 into a date
try:
    expiry_date = datetime.strptime(
        expiry_text,
        "%d%b%Y"
    ).date()
except Exception:
    expiry_date = date.today()

today_ist = datetime.now(IST).date()

# Prevent an invalid minimum date after expiry
minimum_scenario_date = min(today_ist, expiry_date)

st.markdown("### Pre-Expiry Scenario")

scenario_col1, scenario_col2, scenario_col3, scenario_col4 = st.columns(
    [1.2, 1.0, 1.2, 1.0]
)

with scenario_col1:
    scenario_date = st.date_input(
        "Evaluation Date",
        value=minimum_scenario_date,
        min_value=minimum_scenario_date,
        max_value=expiry_date,
        key="scenario_date"
    )

with scenario_col2:
    scenario_time = st.time_input(
        "Evaluation Time",
        value=time(15, 30),
        key="scenario_time"
    )

with scenario_col3:
    iv_mode = st.selectbox(
        "IV Mode",
        [
            "Current IV",
            "Current IV + Change",
            "Manual Common IV"
        ],
        key="iv_mode"
    )

with scenario_col4:
    if iv_mode == "Current IV + Change":
        iv_change = st.number_input(
            "IV Change (%)",
            min_value=-50.0,
            max_value=100.0,
            value=0.0,
            step=0.5,
            key="iv_change"
        )

        manual_common_iv = None

    elif iv_mode == "Manual Common IV":
        manual_common_iv = st.number_input(
            "Common IV (%)",
            min_value=0.1,
            max_value=200.0,
            value=12.0,
            step=0.1,
            key="manual_common_iv"
        )

        iv_change = 0.0

    else:
        iv_change = 0.0
        manual_common_iv = None

scenario_datetime = datetime.combine(
    scenario_date,
    scenario_time
).replace(tzinfo=IST)

# Assume option expiry at 3:30 PM IST
expiry_datetime = datetime.combine(
    expiry_date,
    time(15, 30)
).replace(tzinfo=IST)

remaining_seconds = max(
    (expiry_datetime - scenario_datetime).total_seconds(),
    0
)

scenario_T = max(
    remaining_seconds / (365.0 * 24.0 * 60.0 * 60.0),
    1e-8
)

remaining_days = remaining_seconds / 86400.0

st.caption(
    f"Expiry: {expiry_text or 'Not available'} | "
    f"Evaluation: {scenario_datetime.strftime('%d-%b-%Y %H:%M')} IST | "
    f"Time remaining: {remaining_days:.2f} calendar days"
)
label_col, input_col, blank_col = st.columns([1.2, 1.0, 4.8])

with label_col:
    st.markdown(
        "<div style='padding-top:8px;font-weight:600;'>Number of Legs</div>",
        unsafe_allow_html=True
    )

with input_col:
    if strategy_name == "Custom":
        num_legs = st.number_input(
            "Number of Legs",
            min_value=1,
            max_value=4,
            value=2,
            step=1,
            key="number_of_legs"
        )
    else:
        num_legs = len(selected_template)
        st.markdown(f"**Number of Legs:** {num_legs}")

legs = []

# =========================================================
# COMPLETE LEG DETAILS
# Leg | Buy/Sell | CE/PE | Strike | Lots | Manual | Entry | LTP | MTM
# =========================================================

h1, h2, h3, h4, h5, h6, h7, h8, h9 = st.columns(
    [0.25, 0.82, 0.60, 1.20, 0.50, 0.48, 0.68, 0.58, 0.70]
)

h1.markdown("**Leg**")
h2.markdown("**Buy/Sell**")
h3.markdown("**CE/PE**")
h4.markdown("**Strike**")
h5.markdown("**Lots**")
h6.markdown("**Manual**")
h7.markdown("**Entry**")
h8.markdown("**LTP**")
h9.markdown("**MTM**")


for i in range(1, num_legs + 1):

    template_leg = (
        selected_template[i - 1]
        if strategy_name != "Custom"
        else None
    )
    c0, c1, c2, c3, c4, c5, c6, c7, c8 = st.columns(
        [0.25, 0.82, 0.60, 1.20, 0.50, 0.48, 0.68, 0.58, 0.70]
    )

    # Leg number
    with c0:
        st.markdown(
            f"""
            <div style="
                padding-top:8px;
                font-size:15px;
                font-weight:700;
            ">
                {i}
            </div>
            """,
            unsafe_allow_html=True
        )

    # Buy / Sell
    with c1:
        buy_sell_options = ["BUY", "SELL"]

        buy_sell_index = 0
        if template_leg:
            buy_sell_index = buy_sell_options.index(template_leg["buy_sell"])

        buy_sell = st.selectbox(
            "Buy/Sell",
            buy_sell_options,
            index=buy_sell_index,
            key=f"leg{i}_buy_sell",
            label_visibility="collapsed"
        )

    # CE / PE
    with c2:
        cepe_options = ["CE", "PE"]

        cepe_index = 0
        if template_leg:
            cepe_index = cepe_options.index(template_leg["cepe"])

        cepe = st.selectbox(
            "CE/PE",
            cepe_options,
            index=cepe_index,
            key=f"leg{i}_cepe",
            label_visibility="collapsed"
        )

    # Strike
    with c3:
        if template_leg:
            preferred_strike = atm + template_leg["offset"]

            if preferred_strike in near_strikes:
                default_index = near_strikes.index(preferred_strike)
            else:
                default_index = (
                    near_strikes.index(atm)
                    if atm in near_strikes
                    else len(near_strikes) // 2
                )
        else:
            default_index = (
                near_strikes.index(atm)
                if atm in near_strikes
                else len(near_strikes) // 2
            )

        strike = st.selectbox(
            "Strike",
            near_strikes,
            index=default_index,
            format_func=lambda s: strike_label(s, cepe, atm),
            key=f"leg{i}_strike",
            label_visibility="collapsed"
        )

    # Lots
    with c4:
        default_lots = template_leg["lots"] if template_leg else 1

        lots = st.number_input(
            "Lots",
            min_value=1,
            max_value=50,
            value=default_lots,
            step=1,
            key=f"leg{i}_lots",
            label_visibility="collapsed"
        )

    # Obtain current live LTP
    auto_premium = float(
        get_ltp_for_leg(option_df, strike, cepe)
    )

    # Manual entry selection
    with c5:
        manual = st.checkbox(
            "Manual",
            value=False,
            key=f"leg{i}_manual",
            label_visibility="collapsed"
        )

    # Entry premium
    with c6:
        if manual:
            entry_price = st.number_input(
                "Entry",
                min_value=0.0,
                value=float(auto_premium),
                step=0.05,
                format="%.2f",
                key=f"leg{i}_entry",
                label_visibility="collapsed"
            )
        else:
            entry_price = auto_premium

            st.markdown(
                f"""
                <div style="
                    padding-top:8px;
                    font-size:14px;
                    font-weight:700;
                    white-space:nowrap;
                ">
                    ₹{entry_price:.2f}
                </div>
                """,
                unsafe_allow_html=True
            )

    # MTM calculation
    quantity = lots * LOT_SIZE

    if buy_sell == "BUY":
        mtm = (auto_premium - entry_price) * quantity
    else:
        mtm = (entry_price - auto_premium) * quantity

    # Live LTP display
    with c7:
        st.markdown(
            f"""
            <div style="
                padding-top:8px;
                font-size:14px;
                font-weight:700;
                white-space:nowrap;
            ">
                ₹{auto_premium:.2f}
            </div>
            """,
            unsafe_allow_html=True
        )

    # MTM display
    with c8:
        st.markdown(
            f"""
            <div style="
                padding-top:8px;
                font-size:14px;
                font-weight:700;
                white-space:nowrap;
            ">
                ₹{mtm:,.0f}
            </div>
            """,
            unsafe_allow_html=True
        )

    # Store each leg for payoff calculation
    legs.append({
        "buy_sell": buy_sell,
        "cepe": cepe,
        "strike": strike,
        "lots": lots,
        "manual": manual,
        "entry": entry_price,
        "ltp": auto_premium,
        "mtm": mtm,

        # Existing payoff calculation uses premium
        "premium": entry_price
    })
    
# BLOCK B STARTS HERE — NO INDENTATION

scenario_price_range = list(
    range(
        int(atm - 1000),
        int(atm + 1000) + 50,
        50
    )
)

scenario_rows = []
# ==========================================================
# PRE-EXPIRY SCENARIO CALCULATION
# ==========================================================

def find_column(df, possible_names):
    for column_name in possible_names:
        if column_name in df.columns:
            return column_name
    return None


def get_leg_row(df, strike_value):
    numeric_strikes = pd.to_numeric(
        df["Strike"],
        errors="coerce"
    )

    matching_rows = df.loc[
        numeric_strikes == float(strike_value)
    ]

    if matching_rows.empty:
        return None

    return matching_rows.iloc[0]


def safe_number(value, default=0.0):
    value = pd.to_numeric(value, errors="coerce")

    if pd.isna(value):
        return float(default)

    return float(value)


# ----------------------------------------------------------
# Calculate current strategy Greeks
# ----------------------------------------------------------

# ----------------------------------------------------------
# Calculate strategy Greeks for selected date, time and IV
# ----------------------------------------------------------

net_delta = 0.0
net_theta = 0.0
net_vega = 0.0
net_gamma = 0.0

for leg in legs:

    strike = float(leg["strike"])
    cepe = leg["cepe"]
    quantity = float(leg["lots"]) * LOT_SIZE

    direction = (
        1.0
        if leg["buy_sell"] == "BUY"
        else -1.0
    )

    option_row = get_leg_row(
        option_df,
        strike
    )

    current_iv = 12.0

    if option_row is not None:

        if cepe == "CE":
            iv_column = find_column(
                option_df,
                ["CE IV", "CE_IV"]
            )
        else:
            iv_column = find_column(
                option_df,
                ["PE IV", "PE_IV"]
            )

        if iv_column:
            current_iv = safe_number(
                option_row.get(iv_column),
                default=12.0
            )

            if current_iv <= 0:
                current_iv = 12.0

    if iv_mode == "Manual Common IV":

        scenario_iv_percent = float(
            manual_common_iv
        )

    elif iv_mode == "Current IV + Change":

        scenario_iv_percent = max(
            current_iv + float(iv_change),
            0.1
        )

    else:

        scenario_iv_percent = current_iv

    scenario_iv_decimal = (
        scenario_iv_percent / 100.0
    )

    scenario_greeks = bs_greeks(
        spot=spot_now,
        strike=strike,
        time_years=scenario_T,
        iv=scenario_iv_decimal,
        option_type=cepe
    )

    net_delta += (
        direction
        * scenario_greeks["delta"]
        * quantity
    )

    net_theta += (
        direction
        * scenario_greeks["theta"]
        * quantity
    )

    net_vega += (
        direction
        * scenario_greeks["vega"]
        * quantity
    )

    net_gamma += (
        direction
        * scenario_greeks["gamma"]
        * quantity
    )

# ----------------------------------------------------------
# Calculate selected-date payoff over the spot range
# ----------------------------------------------------------

for scenario_spot in scenario_price_range:

    total_scenario_pl = 0.0

    for leg in legs:

        strike = float(leg["strike"])
        cepe = leg["cepe"]
        quantity = float(leg["lots"]) * LOT_SIZE
        entry_price = float(leg["entry"])

        option_row = get_leg_row(option_df, strike)

        current_iv = 12.0

        if option_row is not None:

            if cepe == "CE":

                iv_column = find_column(
                    option_df,
                    ["CE IV", "CE_IV"]
                )

            else:

                iv_column = find_column(
                    option_df,
                    ["PE IV", "PE_IV"]
                )

            if iv_column:

                current_iv = safe_number(
                    option_row.get(iv_column),
                    default=12.0
                )

                if current_iv <= 0:
                    current_iv = 12.0

        # Choose IV according to dashboard selection
        if iv_mode == "Manual Common IV":

            scenario_iv_percent = float(
                manual_common_iv
            )

        elif iv_mode == "Current IV + Change":

            scenario_iv_percent = max(
                current_iv + float(iv_change),
                0.1
            )

        else:

            scenario_iv_percent = current_iv

        scenario_iv_decimal = (
            scenario_iv_percent / 100.0
        )

        theoretical_price = bs_option_price(
            spot=scenario_spot,
            strike=strike,
            time_years=scenario_T,
            iv=scenario_iv_decimal,
            option_type=cepe
        )

        if leg["buy_sell"] == "BUY":

            leg_scenario_pl = (
                theoretical_price - entry_price
            ) * quantity

        else:

            leg_scenario_pl = (
                entry_price - theoretical_price
            ) * quantity

        total_scenario_pl += leg_scenario_pl

    scenario_rows.append({
        "Spot": scenario_spot,
        "Scenario Payoff": total_scenario_pl
    })


scenario_df = pd.DataFrame(scenario_rows)


# ----------------------------------------------------------
# Strategy balance indication
# ----------------------------------------------------------

if abs(net_delta) <= 5:

    position_bias = "Delta Neutral"

elif net_delta > 5:

    position_bias = "Bullish"

else:

    position_bias = "Bearish"


st.markdown("### Strategy Balance")

g1, g2, g3, g4, g5 = st.columns(5)

g1.metric(
    "Net Delta",
    f"{net_delta:,.2f}"
)

g2.metric(
    "Net Theta",
    f"{net_theta:,.2f}"
)

g3.metric(
    "Net Vega",
    f"{net_vega:,.2f}"
)

g4.metric(
    "Net Gamma",
    f"{net_gamma:,.4f}"
)

g5.metric(
    "Position Bias",
    position_bias
)


# ----------------------------------------------------------
# Scenario P/L near present spot
# ----------------------------------------------------------

nearest_scenario_spot = min(
    scenario_price_range,
    key=lambda value: abs(value - spot_now)
)

scenario_live_pl = scenario_df.loc[
    scenario_df["Spot"] == nearest_scenario_spot,
    "Scenario Payoff"
].iloc[0]

st.metric(
    "Estimated P/L at Selected Date, Time and IV",
    f"₹{scenario_live_pl:,.0f}"
)


# ----------------------------------------------------------
# Selected-date payoff graph
# ----------------------------------------------------------

st.markdown("### Payoff at Selected Date / Time")

fig_scenario = px.line(
    scenario_df,
    x="Spot",
    y="Scenario Payoff",
    title=(
        "Pre-Expiry Payoff — "
        + scenario_datetime.strftime(
            "%d-%b-%Y %H:%M"
        )
        + " IST"
    )
)

fig_scenario.add_vline(
    x=spot_now,
    line_dash="dash",
    annotation_text="Current Spot"
)

fig_scenario.add_hline(
    y=0,
    line_dash="dash"
)

fig_scenario.update_layout(
    height=450,
    xaxis_title="Spot",
    yaxis_title="Profit / Loss ₹"
)

st.plotly_chart(
    fig_scenario,
    width="stretch"
)
# =========================
# PAYOFF CALCULATION
# =========================

price_range = list(range(int(atm - 1000), int(atm + 1000) + 50, 50))
payoff_rows = []

for price in price_range:
    total_payoff = 0

    for leg in legs:
        strike = leg["strike"]
        premium = leg["premium"]
        lots = leg["lots"]
        qty = lots * LOT_SIZE

        if leg["cepe"] == "CE":
            intrinsic = max(price - strike, 0)
        else:
            intrinsic = max(strike - price, 0)

        if leg["buy_sell"] == "BUY":
            leg_payoff = (intrinsic - premium) * qty
        else:
            leg_payoff = (premium - intrinsic) * qty

        total_payoff += leg_payoff

    payoff_rows.append({
        "Spot": price,
        "Payoff": total_payoff
    })

payoff_df = pd.DataFrame(payoff_rows)

# Live P/L near current spot
nearest_spot = min(price_range, key=lambda x: abs(x - spot_now))
live_pl = payoff_df[payoff_df["Spot"] == nearest_spot]["Payoff"].iloc[0]

max_profit = payoff_df["Payoff"].max()
max_loss = payoff_df["Payoff"].min()

c1, c2, c3 = st.columns(3)
c1.metric("Live P/L near Spot", f"₹{live_pl:,.0f}")
c2.metric("Max Profit in Range", f"₹{max_profit:,.0f}")
c3.metric("Max Loss in Range", f"₹{max_loss:,.0f}")

st.markdown(
    "<div style='height:2px'></div>",
    unsafe_allow_html=True
)
st.markdown("### Payoff at Expiry")

fig_payoff = px.line(
    payoff_df,
    x="Spot",
    y="Payoff",
    title="Payoff at Expiry"
)

fig_payoff.add_vline(
    x=spot_now,
    line_dash="dash",
    annotation_text="Spot"
)

fig_payoff.update_layout(
    height=450,
    xaxis_title="Spot",
    yaxis_title="Profit / Loss ₹"
)

st.plotly_chart(fig_payoff, width="stretch")


