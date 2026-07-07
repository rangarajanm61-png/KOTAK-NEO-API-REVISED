from streamlit_autorefresh import st_autorefresh
from st_aggrid import AgGrid, GridOptionsBuilder
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
# import time
from option_chain import calculate_pcr, expiry_summary
from datetime import datetime

st.set_page_config(layout="wide")
st_autorefresh(interval=5000, key="dashboard_refresh")
st.markdown("""
<style>

/* Metric label */
div[data-testid="metric-container"] label {
    font-size: 10px !important;
    font-weight: 500 !important;
}

/* Metric value */
div[data-testid="stMetricValue"] {
    font-size: 16px !important;
    font-weight: 600 !important;
}

/* Reduce padding */
div[data-testid="metric-container"] {
    padding: 2px !important;
}

</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>

[data-testid="stMetricValue"] {
    font-size: 24px;
    font-weight: bold;
}

[data-testid="stMetricLabel"] {
    font-size: 12px;
}

div[data-testid="stMetric"] {
    text-align: center;
}

</style>
""", unsafe_allow_html=True)

placeholder = st.empty()

# temporary storage
if "data" not in st.session_state:
    st.session_state.data = []

# Read NIFTY spot from option_chain.csv Spot column first
try:
    oc = pd.read_csv("option_chain.csv")
    import os, time
    # st.write("option_chain.csv modified:", time.ctime(os.path.getmtime("option_chain.csv")))
    st.write("Option_chain.csv rows:", len(oc))
        
    option_df = oc.copy()

    # ---------- SAFE COLUMN BLOCK : avoid KeyError ----------

    required_cols = [
        "Strike",
        "CE_LTP", "PE_LTP",
        "CE_OI", "PE_OI",
        "CE_VOL", "PE_VOL",
        "OI_PCR", "VOL_PCR",
        "CE_IV", "PE_IV",
        "CE_Delta", "PE_Delta",
        "CE_Theta", "PE_Theta",
        "CE_Gamma", "PE_Gamma",
        "CE_Vega", "PE_Vega"
    ]

    for col in required_cols:
        if col not in option_df.columns:
            option_df[col] = 0

    numeric_cols = [col for col in required_cols if col != "Strike"]

    for col in numeric_cols:
        option_df[col] = pd.to_numeric(option_df[col], errors="coerce").fillna(0)

# ---------- END SAFE COLUMN BLOCK ----------

    option_df["CE OI"] = pd.to_numeric(option_df["CE OI"], errors="coerce").fillna(0)
    option_df["PE OI"] = pd.to_numeric(option_df["PE OI"], errors="coerce").fillna(0)

    total_ce_oi = option_df["CE OI"].sum()
    total_pe_oi = option_df["PE OI"].sum()

    oi_pcr = round(total_pe_oi / total_ce_oi, 2) if total_ce_oi != 0 else 0

except Exception as e:
    st.error(f"Error reading option_chain.csv: {e}")
    st.stop()    
try:
    if "Spot" in option_df.columns:
        spot_series = pd.to_numeric(option_df["Spot"], errors="coerce").dropna()
        nifty_spot = float(spot_series.iloc[-1]) if not spot_series.empty else 0
    else:
        nifty_spot = 0
except Exception:
    nifty_spot = 0


# -------- Max Pain from main.py --------
try:
    hist = pd.read_csv("chart_history.csv")

    if not hist.empty and "Max Pain" in hist.columns:
        valid_mp = pd.to_numeric(hist["Max Pain"], errors="coerce").dropna()

        if not valid_mp.empty:
            max_pain = int(valid_mp.iloc[-1])
        else:
            max_pain = 0
    else:
        max_pain = 0

except Exception:
    max_pain = 0
      
# PCR Calculations
total_ce_oi = option_df["CE OI"].sum()
total_pe_oi = option_df["PE OI"].sum()

total_ce_vol = option_df["CE Volume"].sum()
total_pe_vol = option_df["PE Volume"].sum()

oi_pcr = round(total_pe_oi / total_ce_oi, 2) if total_ce_oi != 0 else 0
vol_pcr = round(total_pe_vol / total_ce_vol, 2) if total_ce_vol != 0 else 0

print(option_df.columns.tolist())

total_ce_oi_change = option_df["CE OI Change"].sum()
total_pe_oi_change = option_df["PE OI Change"].sum()
overall_oi_pcr_change = round(total_pe_oi_change / total_ce_oi_change, 2) if total_ce_oi_change != 0 else 0


with placeholder.container():

    from datetime import datetime

    st.markdown("### NIFTY Option Dashboard")
    st.caption(f"Date : {datetime.now().strftime('%d-%b-%Y')}")
    
    if "Expiry" in option_df.columns:
        expiry_list = sorted(option_df["Expiry"].dropna().unique())
    else:
        expiry_list = ["Current Expiry"]

    title_col, expiry_col = st.columns([8,2])

    with expiry_col:
        selected_expiry = st.selectbox(
            "Expiry",
            expiry_list,
            label_visibility="collapsed"
        )

    if "Expiry" not in option_df.columns:
        option_df["Expiry"] = selected_expiry

    option_df = option_df[option_df["Expiry"] == selected_expiry]
    full_df = pd.read_csv("option_chain.csv")

if "Expiry" not in full_df.columns:
    full_df["Expiry"] = selected_expiry

full_df = full_df[full_df["Expiry"] == selected_expiry].copy()

try:
    hist_df = pd.read_csv("chart_history.csv")
    
except:
    hist_df = pd.DataFrame()

summary_df = pd.DataFrame([{
    "Spot": round(nifty_spot, 2),
    "CE OI (L)": f"{total_ce_oi/100000:.1f}",
    "PE OI (L)": f"{total_pe_oi/100000:.1f}",
    "CE OI Δ (L)": f"{total_ce_oi_change/100000:.1f}",
    "PE OI Δ (L)": f"{total_pe_oi_change/100000:.1f}",
    "OI PCR": f"{oi_pcr:.2f}",
    "PCR Δ": f"{overall_oi_pcr_change:.2f}",
    "Vol PCR": f"{vol_pcr:.2f}",
    "Max Pain": int(hist_df["Max Pain"].iloc[-1]) if not hist_df.empty and "Max Pain" in hist_df.columns else int(max_pain),
    "Expiry": selected_expiry,
    "Last Refresh Time": hist_df["Time"].iloc[-1] if not hist_df.empty and "Time" in hist_df.columns else "",
}])
st.dataframe(
        summary_df,
        width="stretch",
        hide_index=True
    )

    # Strike-wise PCR
option_df["OI PCR"] = option_df.apply(
        lambda r: round(r["PE OI"] / r["CE OI"], 2) if r["CE OI"] != 0 else 0,
        axis=1
    )

option_df["PE/CE Vol Ratio"] = option_df.apply(
        lambda r: round(r["PE Volume"] / r["CE Volume"], 2) if r["CE Volume"] != 0 else 0,
        axis=1
    )

if "CE OI" not in option_df.columns:
    option_df["CE OI"] = 0

if "PE OI" not in option_df.columns:
    option_df["PE OI"] = 0

if "CE Volume" not in option_df.columns:
    option_df["CE Volume"] = 0

if "PE Volume" not in option_df.columns:
    option_df["PE Volume"] = 0

    pcr_df = option_df.copy()

if "Expiry" not in option_df.columns:
    option_df["Expiry"] = "Current Expiry"

option_df = option_df.rename(columns={
    "pExpiryDate": "Expiry",
    "CE_LTP": "CE LTP",
    "PE_LTP": "PE LTP"
})
if "CE OI" not in option_df.columns:
    option_df["CE OI"] = 0
if "PE OI" not in option_df.columns:
    option_df["PE OI"] = 0
if "CE Volume" not in option_df.columns:
    option_df["CE Volume"] = 0
if "PE Volume" not in option_df.columns:
    option_df["PE Volume"] = 0

pcr_df = option_df.copy()

summary_df = expiry_summary(pcr_df)

st.subheader("Table 1 - Price / OI / PCR")

table1_cols = [
    "Strike",
    "CE LTP",
    "CE OI",
    "CE Volume",
    "CE Price Change",
    "CE OI Change",
    "CE OI Change %",
    "PE LTP",
    "PE OI",
    "PE Volume",
    "PE Price Change",
    "PE OI Change",
    "PE OI Change %",
    "OI PCR",
    "OI PCR Change",
    "PE/CE Vol Ratio",
    "Status",
]
display_df = pcr_df[table1_cols].copy()

display_df = display_df.rename(columns={
    "CE Volume": "CE Vol",
    "PE Volume": "PE Vol",
    "CE Price Change": "CE Price Chng",
    "PE Price Change": "PE Price Chng",
    "CE OI Change": "CE OI Chng",
    "PE OI Change": "PE OI Chng",
    "CE OI Change %": "CE OI Chng %",
    "PE OI Change %": "PE OI Chng %",
    "OI PCR Change": "OI PCR Chng",
    "PE/CE Vol Ratio": "PE/CE Vol",
})

# Keep only columns that exist

st.dataframe(display_df, width="stretch", height=620)

# ---------------- LIVE CHARTS ----------------
st.markdown("<br><br><br>", unsafe_allow_html=True)


try:
    hist_df = pd.read_csv("chart_history.csv")
    from datetime import datetime

    if "Date" not in hist_df.columns:
        hist_df["Date"] = datetime.now().strftime("%d-%b-%Y")

    hist_df["Date"] = hist_df["Date"].fillna(datetime.now().strftime("%d-%b-%Y"))

    hist_df = hist_df.dropna(subset=["Time"])
    hist_df = hist_df[hist_df["Time"].astype(str) != "Ellipsis"]
    hist_df = hist_df.tail(500)
    hist_df["Spot"] = pd.to_numeric(hist_df["Spot"], errors="coerce")
    hist_df["OI PCR"] = pd.to_numeric(hist_df["OI PCR"], errors="coerce")
    hist_df["Vol PCR"] = pd.to_numeric(hist_df["Vol PCR"], errors="coerce")
    # st.write("Rows in history:", len(hist_df))
    # st.dataframe(hist_df.tail(5))

    st.markdown("### Live Combined Chart: Spot + PCR")
    
    combo_cols = ["Spot", "Max Pain", "OI PCR", "Vol PCR", "OI PCR Change"]

    combo_df = hist_df[["Time"] + combo_cols].copy()

    for c in combo_cols:
        combo_df[c] = pd.to_numeric(combo_df[c], errors="coerce").fillna(0)

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=combo_df["Time"],
        y=combo_df["Spot"],
        mode="lines",
        name="NIFTY Spot",
        line=dict(color="deepskyblue", width=3),
        yaxis="y1"
    ))

    fig.add_trace(go.Scatter(
    x=combo_df["Time"],
    y=combo_df["Max Pain"],
    mode="lines",
    name="Max Pain",
    line=dict(color="gold", width=3, dash="dash"),
    yaxis="y1"
    ))

    fig.add_trace(go.Scatter(
        x=combo_df["Time"],
        y=combo_df["OI PCR"],
        mode="lines",
        name="OI PCR",
        line=dict(color="red", width=2),
        yaxis="y2"
    ))

    fig.add_trace(go.Scatter(
        x=combo_df["Time"],
        y=combo_df["Vol PCR"],
        mode="lines",
        name="Vol PCR",
        line=dict(color="orange", width=2),
        yaxis="y2"
    ))

    fig.add_trace(go.Scatter(
        x=combo_df["Time"],
        y=combo_df["OI PCR Change"],
        mode="lines",
        name="OI PCR Change",
        line=dict(color="lime", width=2),
        yaxis="y2"
    ))

    fig.update_layout(
        height=500,
        xaxis=dict(title="Time"),
        yaxis=dict(
            title="NIFTY Spot",
            side="left"
        ),
        # 
        yaxis2=dict(
        title="PCR",
        overlaying="y",
        side="right",
        range=[-0.2, 2.0]
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0
        )
    )

    st.plotly_chart(fig, use_container_width=True)
    
except Exception as e:
    st.warning(f"Charts not ready: {e}")
   
    greeks_range = 2000

    table2_df = option_df[
        (option_df["Strike"] >= nifty_spot - greeks_range) &
        (option_df["Strike"] <= nifty_spot + greeks_range)
    ].copy()

st.subheader("TABLE 2 - OPTION GREEKS (ATM ±500)")

table2_cols = [
    "Strike",
    "CE LTP",
    "CE_IV",
    "PE LTP",
    "PE_IV",
    "Spot",
    "CE Delta",
    "CE Gamma",
    "CE Theta",
    "CE Decay",
    "CE Vega",
    "PE Delta",
    "PE Gamma",
    "PE Theta",
    "PE Decay",
    "PE Vega",
]
spot = float(pcr_df["Spot"].iloc[0])
atm = round(spot / 50) * 50

pcr_df = pcr_df[
    (pcr_df["Strike"] >= atm - 500) &
    (pcr_df["Strike"] <= atm + 500)
]
table2_cols = [c for c in table2_cols if c in pcr_df.columns]

st.dataframe(
    pcr_df[table2_cols],
    use_container_width=True,
    height=850
)
total_ce_vol = pd.to_numeric(pcr_df["CE Volume"], errors="coerce").fillna(0).sum()
total_pe_vol = pd.to_numeric(pcr_df["PE Volume"], errors="coerce").fillna(0).sum()

oi_pcr = round(total_pe_oi / total_ce_oi, 2) if total_ce_oi > 0 else 0
vol_pcr = round(total_pe_vol / total_ce_vol, 2) if total_ce_vol > 0 else 0

st.markdown("### Trading Day History")

today = datetime.now().strftime("%d-%b-%Y")

if "Date" in hist_df.columns:
    hist_df = hist_df[hist_df["Date"] == today]

if not hist_df.empty:

    history_cols = [
        "Date",
        "Time",
        "Spot",
        "OI PCR",
        "Vol PCR",
        "OI PCR Change",
        "CE OI Change",
        "PE OI Change",
        "Max Pain"
    ]

    history_cols = [c for c in history_cols if c in hist_df.columns]
    hist_display = hist_df[history_cols].tail(100)

    st.dataframe(hist_display, width="stretch", height=300)

# c1, c2 = st.columns(2)
# c1.metric("OI PCR", oi_pcr)
# c2.metric("Volume PCR", vol_pcr)
# if not df.empty:
#             df["LTP"] = pd.to_numeric(df["LTP"], errors="coerce")
#             df = df.dropna(subset=["LTP"])

#             df = df[df["Symbol"].str.contains("CE|PE", na=False)]

#             ce_data = df[df["Symbol"].str.contains("CE", na=False)]
#             pe_data = df[df["Symbol"].str.contains("PE", na=False)]

#             ce_ltp = float(ce_data["LTP"].iloc[-1]) if not ce_data.empty else 0
#             pe_ltp = float(pe_data["LTP"].iloc[-1]) if not pe_data.empty else 0

#             combined = ce_ltp + pe_ltp

#             ce_vol_display = f"{total_ce_vol/100000:.2f}L"
#             pe_vol_display = f"{total_pe_vol/100000:.2f}L"
#             ce_oi_display = f"{total_ce_oi/100000:.2f}L"
#             pe_oi_display = f"{total_pe_oi/100000:.2f}L"
            
#             if oi_pcr > 1.2 and vol_pcr > 1.2:
#                 signal = "STRONG BULL"
#             elif oi_pcr < 0.8 and vol_pcr < 0.8:
#                 signal = "STRONG BEAR"
#             else:
#                 signal = "NEUTRAL"
           
                        
#             left_col, right_col = st.columns([2, 2])

#             with left_col:
#                 st.subheader("Live Tick Table")
#                 st.dataframe(df.tail(8), width="stretch", height=220)

#             with right_col:
#                 st.subheader("LTP Chart")
#             df = df.tail(300)
#             chart_df = df.pivot_table(
#                 index="Time",
#                 columns="Symbol",
#                 values="LTP",
#                 aggfunc="last"
#             )
#             chart_df = chart_df.tail(100)

#             st.line_chart(chart_df)
            
            # time.sleep(5)