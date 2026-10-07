import datetime as dt

import plotly.graph_objects as go
import streamlit as st

import core

st.set_page_config(page_title="Stock Efficiency Explorer", page_icon="📈", layout="wide")

RIYADH = dt.timezone(dt.timedelta(hours=3))


@st.cache_data(ttl=3600, show_spinner=False)
def get_data():
    """Downloads fresh prices from Yahoo Finance. Cached for 1 hour so the page stays fast."""
    metrics, failed = core.load_market_data()
    stamp = dt.datetime.now(RIYADH).strftime("%d %b %Y, %H:%M")
    return metrics, failed, stamp


st.title("📈 Stock Efficiency Explorer")
st.caption(
    "Ranks stocks by how much growth they gave for the risk taken, over the last 12 months. "
    "Prices are downloaded from Yahoo Finance when the page loads and refreshed every hour. "
    "Student project, not investment advice."
)

# ---------------------------------------------------------------- sidebar
with st.sidebar:
    st.header("Your limits")
    market = st.radio("Market", ["US", "Saudi", "Both"], index=2, horizontal=True)
    min_growth = st.number_input("Minimum growth (% over 12 months)", value=5.0, step=1.0)
    max_risk = st.number_input("Maximum risk score (% daily swing)", value=2.5, min_value=0.1, step=0.1)
    top_n = st.slider("How many stocks to show", 5, 30, 10)

    st.divider()
    st.header("Efficiency calculator")
    st.caption("Try any numbers you like.")
    c_growth = st.number_input("Growth %", value=20.0, step=1.0, key="cg")
    c_risk = st.number_input("Risk score %", value=2.0, min_value=0.01, step=0.1, key="cr")
    st.metric("Efficiency score", f"{c_growth / c_risk:.2f}", help="Growth divided by risk")

    st.divider()
    if st.button("Refresh data now"):
        get_data.clear()
        st.rerun()

# ---------------------------------------------------------------- data
try:
    with st.spinner("Downloading the latest prices (the first load can take about a minute)..."):
        df, failed, stamp = get_data()
except Exception as e:
    st.error(f"Could not get data from Yahoo Finance right now. {e}")
    st.stop()

n_us = int((df["Market"] == "US").sum())
n_sa = int((df["Market"] == "Saudi").sum())
st.caption(f"Data last updated: **{stamp} (Riyadh time)** · {len(df)} stocks loaded "
           f"({n_us} US, {n_sa} Saudi) · {len(failed)} could not be loaded")

pool = df if market == "Both" else df[df["Market"] == market]
fits = pool[(pool["Risk"] < max_risk) & (pool["Growth"] > min_growth)].sort_values(
    "Efficiency", ascending=False)
top = fits.head(top_n).reset_index(drop=True)

# ---------------------------------------------------------------- results
k1, k2, k3, k4 = st.columns(4)
k1.metric("Stocks in this market", len(pool))
k2.metric("Stocks that fit your limits", len(fits))
if top.empty:
    k3.metric("Best pick", "None")
    k4.metric("Efficiency", "-")
    st.warning("No stock fits these limits. Try a higher maximum risk or a lower minimum growth.")
else:
    best = top.iloc[0]
    k3.metric("Best pick", best["Company"])
    k3.caption(f"{best['Market']} · {best['Ticker']}")
    k4.metric("Efficiency", f"{best['Efficiency']:.2f}")
    k4.caption(f"growth {best['Growth']:.1f}% · risk {best['Risk']:.2f}")

    st.subheader(f"Top {len(top)} by efficiency")
    show = top.copy()
    show.insert(0, "Rank", range(1, len(show) + 1))
    show = show.rename(columns={"Growth": "Growth %", "Risk": "Risk score",
                                "Efficiency": "Efficiency score"})
    st.dataframe(show, hide_index=True, width="stretch")

    st.subheader("Growth and risk of the top picks")
    fig = go.Figure()
    fig.add_bar(x=top["Company"], y=top["Growth"], name="Growth %", marker_color="#2e7d32")
    fig.add_bar(x=top["Company"], y=top["Risk"], name="Risk score", marker_color="#c62828")
    fig.update_layout(barmode="group", template="plotly_white", height=380,
                      margin=dict(l=10, r=10, t=10, b=10),
                      legend=dict(orientation="h", y=1.1))
    st.plotly_chart(fig, width="stretch")

st.subheader("Every stock: growth vs risk")
rest = pool.drop(fits.index, errors="ignore")
fig2 = go.Figure()
fig2.add_scatter(x=rest["Risk"], y=rest["Growth"], mode="markers", name="Outside your limits",
                 text=rest["Company"], marker=dict(color="#b0b7c3", size=7),
                 hovertemplate="<b>%{text}</b><br>Risk %{x}<br>Growth %{y}%<extra></extra>")
fig2.add_scatter(x=fits["Risk"], y=fits["Growth"], mode="markers", name="Fit your limits",
                 text=fits["Company"], marker=dict(color="#1a237e", size=9),
                 hovertemplate="<b>%{text}</b><br>Risk %{x}<br>Growth %{y}%<extra></extra>")
fig2.add_vline(x=max_risk, line_dash="dash", line_color="#c62828")
fig2.add_hline(y=min_growth, line_dash="dash", line_color="#2e7d32")
fig2.update_layout(template="plotly_white", height=460, margin=dict(l=10, r=10, t=10, b=10),
                   xaxis_title="Risk score (average daily price swing, %)",
                   yaxis_title="Growth over 12 months (%)",
                   legend=dict(orientation="h", y=1.08))
st.plotly_chart(fig2, width="stretch")
st.caption("Stocks in the top-left corner (high growth, low risk) have the best efficiency.")

with st.expander("How it works"):
    st.markdown(
        """
- **Growth %**: how much the price changed from the first to the last trading day of the last 12 months.
- **Risk score**: the average daily price swing, worked out each day as (highest price − lowest price) ÷ opening price, then averaged. A score of 2 means the price typically moves about 2% within a day. It is a simple measure, not a full volatility model.
- **Efficiency score**: growth ÷ risk. A higher number means more growth for each unit of risk.
- **Your limits**: only stocks with risk below your maximum and growth above your minimum are ranked.
- **Stocks covered**: the S&P 500, the Nasdaq-100 and 16 large Saudi companies on Tadawul.
- **Data**: Yahoo Finance through the `yfinance` library. Prices can be delayed, and a few tickers may be missing on any given day.
- Built in Python (pandas, Plotly, Streamlit). I used AI tools to help write and debug the code and I checked the results myself.

This is a student project. It is not investment advice. Past performance does not predict future results.
"""
    )
