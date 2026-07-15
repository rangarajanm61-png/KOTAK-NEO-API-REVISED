from streamlit_autorefresh import st_autorefresh
from st_aggrid import AgGrid, GridOptionsBuilder
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import plotly.express as px
# import time
# from option_chain import calculate_pcr, expiry_summary
from datetime import datetime
from zoneinfo import ZoneInfo

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


