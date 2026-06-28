from streamlit_autorefresh import st_autorefresh
from st_aggrid import AgGrid, GridOptionsBuilder
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
# import time
from option_chain import calculate_pcr, expiry_summary
from datetime import datetime

st.set_page_config(layout="wide")
st_autorefresh(interval=30000, key="dashboard_refresh")
# st.caption(f"Last dashboard refresh: {datetime.now().strftime('%H:%M:%S')}")
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

# Read latest LTP file
def read_ltp():
    try:
        df = pd.read_csv("live_ltp.csv")

        df["OI"] = df["OI"].fillna(0)
        df["VOL"] = df["VOL"].fillna(0)
        return df
    except:
        return pd.DataFrame(columns=["Time", "Symbol", "Token", "LTP", "VOL", "OI"])

df = read_ltp()

# Read NIFTY spot from option_chain.csv Spot column first
try:
    oc = pd.read_csv("option_chain.csv")
        
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
    
    if "Spot" in oc.columns:
        nifty_spot = float(oc["Spot"].dropna().max())
        print("SPOT COLUMN FOUND =", nifty_spot)
    else:
        nifty_row = df[df["Symbol"].str.contains("NIFTY 50|NIFTY", na=False)]
        nifty_spot = float(nifty_row["LTP"].iloc[-1]) if not nifty_row.empty else 0
except:
        nifty_spot = "NA"

def calculate_max_pain(df):
    strikes = sorted(df["Strike"].dropna().unique())
    pain_list = []

    for expiry_price in strikes:
        ce_pain = ((df["Strike"] - expiry_price).clip(lower=0) * df["CE OI"]).sum()
        pe_pain = ((expiry_price - df["Strike"]).clip(lower=0) * df["PE OI"]).sum()
        total_pain = ce_pain + pe_pain
        pain_list.append((expiry_price, total_pain))

    pain_df = pd.DataFrame(pain_list, columns=["Strike", "Total Pain"])
    return pain_df.loc[pain_df["Total Pain"].idxmin(), "Strike"]

max_pain = calculate_max_pain(oc)

# PCR Calculations
total_ce_oi = option_df["CE OI"].sum()
total_pe_oi = option_df["PE OI"].sum()

total_ce_vol = option_df["CE Volume"].sum()
total_pe_vol = option_df["PE Volume"].sum()

oi_pcr = round(total_pe_oi / total_ce_oi, 2) if total_ce_oi != 0 else 0
vol_pcr = round(total_pe_vol / total_ce_vol, 2) if total_ce_vol != 0 else 0

overall_oi_pcr_change = (
    round(option_df["OI PCR Change"].sum(), 2)
    if "OI PCR Change" in option_df.columns
    else 0
)

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
            "",
            expiry_list,
            label_visibility="collapsed"
        )

    if "Expiry" not in option_df.columns:
        option_df["Expiry"] = selected_expiry

    option_df = option_df[option_df["Expiry"] == selected_expiry]

    summary_df = pd.DataFrame([{
        "Spot": round(nifty_spot, 2),
        "CE OI (L)": f"{total_ce_oi/100000:.1f}",
        "PE OI (L)": f"{total_pe_oi/100000:.1f}",
        "OI PCR": f"{oi_pcr:.2f}",
        "PCR Δ": f"{overall_oi_pcr_change:.2f}",
        "Vol PCR": f"{vol_pcr:.2f}",
        "Max Pain": int(max_pain),
        "Expiry": selected_expiry,
        "Last Refresh Time ": datetime.now().strftime("%H:%M:%S")
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

    # st.markdown("### 1. NIFTY Spot vs Time")
    # st.line_chart(hist_df.set_index("Time")[["Spot"]], height=250)

    # st.markdown("### 2. OI PCR vs Time")
    # st.line_chart(hist_df.set_index("Time")[["OI PCR"]], height=250)

    # st.markdown("### 3. Volume PCR vs Time")
    # st.line_chart(hist_df.set_index("Time")[["Vol PCR"]], height=250)

    # st.markdown("### 4. OI PCR Change vs Time")
    # st.line_chart(hist_df.set_index("Time")[["OI PCR Change"]], height=250)

    st.markdown("### Live Combined Chart: Spot + PCR")
    
    combo_cols = ["Spot", "OI PCR", "Vol PCR", "OI PCR Change"]

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
        y=[max_pain] * len(combo_df),
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

st.subheader("Table 2 - Greeks")

table2_cols = [
    "Strike",
    "CE LTP",
    "PE LTP",
    "Spot",
    "CE Delta",
    "CE Gamma",
    "CE Theta",
    "CE Vega",
    "PE Delta",
    "PE Gamma",
    "PE Theta",
    "PE Vega",
]

table2_cols = [c for c in table2_cols if c in pcr_df.columns]

st.dataframe(
    pcr_df[table2_cols],
    use_container_width=True
)
total_ce_vol = pd.to_numeric(pcr_df["CE Volume"], errors="coerce").fillna(0).sum()
total_pe_vol = pd.to_numeric(pcr_df["PE Volume"], errors="coerce").fillna(0).sum()

oi_pcr = round(total_pe_oi / total_ce_oi, 2) if total_ce_oi > 0 else 0
vol_pcr = round(total_pe_vol / total_ce_vol, 2) if total_ce_vol > 0 else 0

# c1, c2 = st.columns(2)
# c1.metric("OI PCR", oi_pcr)
# c2.metric("Volume PCR", vol_pcr)
if not df.empty:
            df["LTP"] = pd.to_numeric(df["LTP"], errors="coerce")
            df = df.dropna(subset=["LTP"])

            df = df[df["Symbol"].str.contains("CE|PE", na=False)]

            ce_data = df[df["Symbol"].str.contains("CE", na=False)]
            pe_data = df[df["Symbol"].str.contains("PE", na=False)]

            ce_ltp = float(ce_data["LTP"].iloc[-1]) if not ce_data.empty else 0
            pe_ltp = float(pe_data["LTP"].iloc[-1]) if not pe_data.empty else 0

            combined = ce_ltp + pe_ltp

            ce_vol_display = f"{total_ce_vol/100000:.2f}L"
            pe_vol_display = f"{total_pe_vol/100000:.2f}L"
            ce_oi_display = f"{total_ce_oi/100000:.2f}L"
            pe_oi_display = f"{total_pe_oi/100000:.2f}L"
            
            if oi_pcr > 1.2 and vol_pcr > 1.2:
                signal = "STRONG BULL"
            elif oi_pcr < 0.8 and vol_pcr < 0.8:
                signal = "STRONG BEAR"
            else:
                signal = "NEUTRAL"
           
            # col1, col2, col3, col4 = st.columns(4)
            # col1.metric("LTP Ratio", round(pe_ltp / ce_ltp, 2) if ce_ltp != 0 else 0)
            # col2.metric("OI PCR", oi_pcr)
            # col3.metric("Vol PCR", vol_pcr)
            # col4.metric("Signal", signal)

            # col5, col6, col7, col8 = st.columns(4)
            # col5.metric("CE OI", ce_oi_display)
            # col6.metric("PE OI", pe_oi_display)
            # col7.metric("CE Vol", ce_vol_display)
            # col8.metric("PE Vol", pe_vol_display)
            
            left_col, right_col = st.columns([2, 2])

            with left_col:
                st.subheader("Live Tick Table")
                st.dataframe(df.tail(8), width="stretch", height=220)

            with right_col:
                st.subheader("LTP Chart")
            df = df.tail(300)
            chart_df = df.pivot_table(
                index="Time",
                columns="Symbol",
                values="LTP",
                aggfunc="last"
            )
            chart_df = chart_df.tail(100)

            st.line_chart(chart_df)
            
            # time.sleep(5)