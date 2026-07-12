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

# </style>
# """, unsafe_allow_html=True)


# st.markdown("""
# <style>

# [data-testid="stMetricValue"] {
#     font-size: 24px;
#     font-weight: bold;
# }

# [data-testid="stMetricLabel"] {
#     font-size: 12px;
# }

# div[data-testid="stMetric"] {
#     text-align: center;
# }
st.markdown("""
<style>

# /* Reduce page margins */

.block-container {
    padding-top: 0rem !important;
    padding-bottom: 0.5rem !important;
    padding-left: 1rem !important;
    padding-right: 1rem !important;
}

# /* Reduce heading spacing */
# h1, h2, h3 {
#     margin-top: 0.15rem !important;
#     margin-bottom: 0.25rem !important;
# }

# /* Compact widget labels */
# div[data-testid="stWidgetLabel"] p {
#     font-size: 11px !important;
#     margin-bottom: 0 !important;
# }

# /* Compact dropdown and input height */
# div[data-baseweb="select"] > div {
#     min-height: 34px !important;
# }

# div[data-testid="stNumberInput"] input {
#     min-height: 34px !important;
# }

# /* Reduce vertical gaps between Streamlit elements */
# div[data-testid="stVerticalBlock"] {
#     gap: 0.35rem !important;
# }

# /* Compact metrics */
# div[data-testid="stMetric"] {
#     padding: 0.15rem 0.35rem !important;
# }

# div[data-testid="stMetricLabel"] {
#     font-size: 11px !important;
# }

# div[data-testid="stMetricValue"] {
#     font-size: 20px !important;
# }

# /* Compact buttons */
# .stButton > button {
#     padding: 0.25rem 0.65rem !important;
#     min-height: 32px !important;
# }

# /* Reduce separator spacing */
# hr {
#     margin-top: 0.3rem !important;
#     margin-bottom: 0.3rem !important;
# }

</style>
""", unsafe_allow_html=True)


# @st.fragment(run_every="30s")
# def refresh_dashboard():
#     st.write(
#         "Dashboard rerun:",
#         datetime.now(IST).strftime("%H:%M:%S")
#     )
#     placeholder = st.empty()

#     # temporary storage
#     if "data" not in st.session_state:
#         st.session_state.data = []

#     # Read NIFTY spot from option_chain.csv Spot column first
#     try:
#         oc = pd.read_csv("option_chain.csv")
#         import os, time
#         # st.write("option_chain.csv modified:", time.ctime(os.path.getmtime("option_chain.csv")))
#         st.write("Option_chain.csv rows:", len(oc))
            
#         option_df = oc.copy()

#         # ---------- SAFE COLUMN BLOCK : avoid KeyError ----------

#         required_cols = [
#             "Strike",
#             "CE_LTP", "PE_LTP",
#             "CE_OI", "PE_OI",
#             "CE_VOL", "PE_VOL",
#             "OI_PCR", "VOL_PCR",
#             "CE_IV", "PE_IV",
#             "CE_Delta", "PE_Delta",
#             "CE_Theta", "PE_Theta",
#             "CE_Gamma", "PE_Gamma",
#             "CE_Vega", "PE_Vega"
#         ]

#         for col in required_cols:
#             if col not in option_df.columns:
#                 option_df[col] = 0

#         numeric_cols = [col for col in required_cols if col != "Strike"]

#         for col in numeric_cols:
#             option_df[col] = pd.to_numeric(option_df[col], errors="coerce").fillna(0)

#     # ---------- END SAFE COLUMN BLOCK ----------

#         option_df["CE OI"] = pd.to_numeric(option_df["CE OI"], errors="coerce").fillna(0)
#         option_df["PE OI"] = pd.to_numeric(option_df["PE OI"], errors="coerce").fillna(0)

#         total_ce_oi = option_df["CE OI"].sum()
#         total_pe_oi = option_df["PE OI"].sum()

#         oi_pcr = round(total_pe_oi / total_ce_oi, 2) if total_ce_oi != 0 else 0

#     except Exception as e:
#         st.error(f"Error reading option_chain.csv: {e}")
#         st.stop()    
#     try:
#         if "Spot" in option_df.columns:
#             spot_series = pd.to_numeric(option_df["Spot"], errors="coerce").dropna()
#             nifty_spot = float(spot_series.iloc[-1]) if not spot_series.empty else 0
#         else:
#             nifty_spot = 0
#     except Exception:
#         nifty_spot = 0

#     # -------- Max Pain from main.py --------
#     try:
#         hist = pd.read_csv("chart_history.csv")

#         if not hist.empty and "Max Pain" in hist.columns:
#             valid_mp = pd.to_numeric(hist["Max Pain"], errors="coerce").dropna()

#             if not valid_mp.empty:
#                 max_pain = int(valid_mp.iloc[-1])
#             else:
#                 max_pain = 0
#         else:
#             max_pain = 0

#     except Exception:
#         max_pain = 0
        
#     # PCR Calculations
#     total_ce_oi = option_df["CE OI"].sum()
#     total_pe_oi = option_df["PE OI"].sum()

#     total_ce_vol = option_df["CE Volume"].sum()
#     total_pe_vol = option_df["PE Volume"].sum()

#     oi_pcr = round(total_pe_oi / total_ce_oi, 2) if total_ce_oi != 0 else 0
#     vol_pcr = round(total_pe_vol / total_ce_vol, 2) if total_ce_vol != 0 else 0

#     # print(option_df.columns.tolist())

#     total_ce_oi_change = option_df["CE OI Change"].sum()
#     total_pe_oi_change = option_df["PE OI Change"].sum()
#     overall_oi_pcr_change = round(total_pe_oi_change / total_ce_oi_change, 2) if total_ce_oi_change != 0 else 0

#     with placeholder.container():

        
#         st.markdown("### NIFTY Option Dashboard")
#         st.caption(f"Date : {datetime.now(IST).strftime('%d-%b-%Y')}")
        
#         if "Expiry" in option_df.columns:
#             expiry_list = sorted(option_df["Expiry"].dropna().unique())
#         else:
#             expiry_list = ["Current Expiry"]

#         title_col, expiry_col = st.columns([8,2])

#         with expiry_col:
#             selected_expiry = st.selectbox(
#                 "Expiry",
#                 expiry_list,
#                 label_visibility="collapsed"
#             )

#         if "Expiry" not in option_df.columns:
#             option_df["Expiry"] = selected_expiry

#         option_df = option_df[option_df["Expiry"] == selected_expiry]
#         full_df = pd.read_csv("option_chain.csv")

#         if "Expiry" not in full_df.columns:
#             full_df["Expiry"] = selected_expiry

#         full_df = full_df[full_df["Expiry"] == selected_expiry].copy()

#         try:
#             hist_df = pd.read_csv("chart_history.csv")
            
#         except:
#             hist_df = pd.DataFrame()

#         summary_df = pd.DataFrame([{
#             "Spot": round(nifty_spot, 2),
#             "CE OI (L)": f"{total_ce_oi/100000:.1f}",
#             "PE OI (L)": f"{total_pe_oi/100000:.1f}",
#             "CE OI Δ (L)": f"{total_ce_oi_change/100000:.1f}",
#             "PE OI Δ (L)": f"{total_pe_oi_change/100000:.1f}",
#             "OI PCR": f"{oi_pcr:.2f}",
#             "PCR Δ": f"{overall_oi_pcr_change:.2f}",
#             "Vol PCR": f"{vol_pcr:.2f}",
#             "Max Pain": int(hist_df["Max Pain"].iloc[-1]) if not hist_df.empty and "Max Pain" in hist_df.columns else int(max_pain),
#             "Expiry": selected_expiry,
#             "Data Time": hist_df["Time"].iloc[-1] if not hist_df.empty else "",
#             "Dashboard Time": datetime.now(IST).strftime("%H:%M:%S")
#         }])
#         st.dataframe(
#                 summary_df,
#                 width="stretch",
#                 hide_index=True
#             )

#         # Strike-wise PCR
#         option_df["OI PCR"] = option_df.apply(
#                 lambda r: round(r["PE OI"] / r["CE OI"], 2) if r["CE OI"] != 0 else 0,
#                 axis=1
#             )

#         option_df["PE/CE Vol Ratio"] = option_df.apply(
#                 lambda r: round(r["PE Volume"] / r["CE Volume"], 2) if r["CE Volume"] != 0 else 0,
#                 axis=1
#             )

#         if "CE OI" not in option_df.columns:
#             option_df["CE OI"] = 0

#         if "PE OI" not in option_df.columns:
#             option_df["PE OI"] = 0

#         if "CE Volume" not in option_df.columns:
#             option_df["CE Volume"] = 0

#         if "PE Volume" not in option_df.columns:
#             option_df["PE Volume"] = 0

#             pcr_df = option_df.copy()

#         if "Expiry" not in option_df.columns:
#             option_df["Expiry"] = "Current Expiry"

#         option_df = option_df.rename(columns={
#             "pExpiryDate": "Expiry",
#             "CE_LTP": "CE LTP",
#             "PE_LTP": "PE LTP"
#         })
#         if "CE OI" not in option_df.columns:
#             option_df["CE OI"] = 0
#         if "PE OI" not in option_df.columns:
#             option_df["PE OI"] = 0
#         if "CE Volume" not in option_df.columns:
#             option_df["CE Volume"] = 0
#         if "PE Volume" not in option_df.columns:
#             option_df["PE Volume"] = 0

#         pcr_df = option_df.copy()

#         try:
#             summary_df = pd.read_csv("summary.csv")
#         except Exception as e:
#             st.warning(f"summary.csv not ready: {e}")
#             summary_df = pd.DataFrame()

#         st.subheader("Table 1 - Price / OI / PCR")

#         table1_cols = [
#             "Strike",
#             "CE LTP",
#             "CE OI",
#             "CE Volume",
#             "CE Price Change",
#             "CE OI Change",
#             "CE OI Change %",
#             "PE LTP",
#             "PE OI",
#             "PE Volume",
#             "PE Price Change",
#             "PE OI Change",
#             "PE OI Change %",
#             "OI PCR",
#             "OI PCR Change",
#             "PE/CE Vol Ratio",
#             "Status",
#         ]
#         display_df = pcr_df[table1_cols].copy()

#         display_df = display_df.rename(columns={
#             "CE Volume": "CE Vol",
#             "PE Volume": "PE Vol",
#             "CE Price Change": "CE Price Chng",
#             "PE Price Change": "PE Price Chng",
#             "CE OI Change": "CE OI Chng",
#             "PE OI Change": "PE OI Chng",
#             "CE OI Change %": "CE OI Chng %",
#             "PE OI Change %": "PE OI Chng %",
#             "OI PCR Change": "OI PCR Chng",
#             "PE/CE Vol Ratio": "PE/CE Vol",
#         })

#     # Keep only columns that exist

#         st.dataframe(display_df, width="stretch", height=620)

#         # ---------------- LIVE CHARTS ----------------
#         st.markdown("<br><br><br>", unsafe_allow_html=True)


#         try:
#             hist_df = pd.read_csv("chart_history.csv")
            
#             if "Date" not in hist_df.columns:
#                 hist_df["Date"] = datetime.now(IST).strftime("%d-%b-%Y")

#             hist_df["Date"] = hist_df["Date"].fillna(datetime.now(IST).strftime("%d-%b-%Y"))

#             hist_df = hist_df.dropna(subset=["Time"])
#             hist_df = hist_df[hist_df["Time"].astype(str) != "Ellipsis"]
#             hist_df = hist_df.tail(500)
#             hist_df["Spot"] = pd.to_numeric(hist_df["Spot"], errors="coerce")
#             hist_df["OI PCR"] = pd.to_numeric(hist_df["OI PCR"], errors="coerce")
#             hist_df["Vol PCR"] = pd.to_numeric(hist_df["Vol PCR"], errors="coerce")
#             # st.write("Rows in history:", len(hist_df))
#             # st.dataframe(hist_df.tail(5))

#             st.markdown("### Live Combined Chart: Spot + PCR")
            
#             combo_cols = ["Spot", "Max Pain", "OI PCR", "Vol PCR", "OI PCR Change"]

#             combo_df = hist_df[["Time"] + combo_cols].copy()

#             for c in combo_cols:
#                 combo_df[c] = pd.to_numeric(combo_df[c], errors="coerce").fillna(0)

#             fig = go.Figure()

#             fig.add_trace(go.Scatter(
#                 x=combo_df["Time"],
#                 y=combo_df["Spot"],
#                 mode="lines",
#                 name="NIFTY Spot",
#                 line=dict(color="deepskyblue", width=3),
#                 yaxis="y1"
#             ))

#             fig.add_trace(go.Scatter(
#             x=combo_df["Time"],
#             y=combo_df["Max Pain"],
#             mode="lines",
#             name="Max Pain",
#             line=dict(color="gold", width=3, dash="dash"),
#             yaxis="y1"
#             ))

#             fig.add_trace(go.Scatter(
#                 x=combo_df["Time"],
#                 y=combo_df["OI PCR"],
#                 mode="lines",
#                 name="OI PCR",
#                 line=dict(color="red", width=2),
#                 yaxis="y2"
#             ))

#             fig.add_trace(go.Scatter(
#                 x=combo_df["Time"],
#                 y=combo_df["Vol PCR"],
#                 mode="lines",
#                 name="Vol PCR",
#                 line=dict(color="orange", width=2),
#                 yaxis="y2"
#             ))

#             fig.add_trace(go.Scatter(
#                 x=combo_df["Time"],
#                 y=combo_df["OI PCR Change"],
#                 mode="lines",
#                 name="OI PCR Change",
#                 line=dict(color="lime", width=2),
#                 yaxis="y2"
#             ))

#             fig.update_layout(
#                 height=500,
#                 xaxis=dict(title="Time"),
#                 yaxis=dict(
#                     title="NIFTY Spot",
#                     side="left"
#                 ),
#                 # 
#                 yaxis2=dict(
#                 title="PCR",
#                 overlaying="y",
#                 side="right",
#                 range=[-0.2, 2.0]
#                 ),
#                 legend=dict(
#                     orientation="h",
#                     yanchor="bottom",
#                     y=1.02,
#                     xanchor="left",
#                     x=0
#                 )
#             )

#             st.plotly_chart(fig, width="stretch")
            
#         except Exception as e:
#             st.warning(f"Charts not ready: {e}")
        
#             greeks_range = 2000

#             table2_df = option_df[
#                 (option_df["Strike"] >= nifty_spot - greeks_range) &
#                 (option_df["Strike"] <= nifty_spot + greeks_range)
#             ].copy()

#         st.subheader("TABLE 2 - OPTION GREEKS (ATM ±500)")

#         table2_cols = [
#             "Strike",
#             "CE LTP",
#             "CE_IV",
#             "PE LTP",
#             "PE_IV",
#             "Spot",
#             "CE Delta",
#             "CE Gamma",
#             "CE Theta",
#             "CE Decay",
#             "CE Vega",
#             "PE Delta",
#             "PE Gamma",
#             "PE Theta",
#             "PE Decay",
#             "PE Vega",
#         ]
#         spot = float(pcr_df["Spot"].iloc[0])
#         atm = round(spot / 50) * 50

#         pcr_df = pcr_df[
#             (pcr_df["Strike"] >= atm - 500) &
#             (pcr_df["Strike"] <= atm + 500)
#         ]
#         table2_cols = [c for c in table2_cols if c in pcr_df.columns]

#         st.dataframe(
#             pcr_df[table2_cols],
#             width="stretch",
#             height=850
#         )
#         total_ce_vol = pd.to_numeric(pcr_df["CE Volume"], errors="coerce").fillna(0).sum()
#         total_pe_vol = pd.to_numeric(pcr_df["PE Volume"], errors="coerce").fillna(0).sum()

#         oi_pcr = round(total_pe_oi / total_ce_oi, 2) if total_ce_oi > 0 else 0
#         vol_pcr = round(total_pe_vol / total_ce_vol, 2) if total_ce_vol > 0 else 0

#         st.markdown("### Trading Day History")

#         today = datetime.now(IST).strftime("%d-%b-%Y")

#         if "Date" in hist_df.columns:
#             hist_df = hist_df[hist_df["Date"] == today]

#         if not hist_df.empty:

#             history_cols = [
#                 "Date",
#                 "Time",
#                 "Spot",
#                 "OI PCR",
#                 "Vol PCR",
#                 "OI PCR Change",
#                 "CE OI Change",
#                 "PE OI Change",
#                 "Max Pain"
#             ]

#             history_cols = [c for c in history_cols if c in hist_df.columns]
#             hist_display = hist_df[history_cols].tail(100)

#             st.dataframe(hist_display, width="stretch", height=300)

# refresh_dashboard()

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

# st.subheader("Table 3 - Payoff Calculator")

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

title_col, time_col = st.columns([3, 2])

with title_col:
    st.markdown(
        "<h2 style='margin:0; padding:0;'>"
        "Table 3 - Payoff Calculator"
        "</h2>",
        unsafe_allow_html=True
    )

with time_col:
    st.markdown(
        f"""
        <div style="
            text-align:right;
            padding-top:8px;
            font-size:13px;
            white-space:nowrap;
        ">
            Last Refresh : {now.strftime('%d-%b %H:%M:%S IST')}
        </div>
        """,
        unsafe_allow_html=True
    )
spot_col, atm_col, refresh_col = st.columns([2, 1, 1])

with spot_col:
    st.markdown("**Current Spot**")
    st.markdown(
        f"<div style='font-size:18px;font-weight:700'>{spot_now:.2f}</div>",
        unsafe_allow_html=True
    )

with atm_col:
    st.markdown("**ATM**")
    st.markdown(
        f"<div style='font-size:18px;font-weight:700'>{atm}</div>",
        unsafe_allow_html=True
    )
    
with refresh_col:
    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)
    if st.button("Refresh LTP", key="refresh_payoff_data"):
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


