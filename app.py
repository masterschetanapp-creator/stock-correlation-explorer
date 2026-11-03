"""
Stock Correlation Explorer — Streamlit Web Application
Multi-Factor Market Interrelation & Predictive Sensitivity Engine
Deployable to Streamlit Community Cloud (share.streamlit.io)
"""

import math
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import xml.etree.ElementTree as ET

import numpy as np
import pandas as pd
import requests
import yfinance as yf
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ---------------------------------------------------------------------------
# 1. Page Configuration & Custom Theme
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Stock Correlation Explorer | NSE & BSE Multi-Factor Engine",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom High-Contrast Financial Aesthetics
st.markdown("""
<style>
    .reportview-container, .main {
        background-color: #0a0e17;
        color: #d1d4dc;
    }
    .stApp {
        background-color: #0a0e17;
    }
    div[data-testid="stSidebar"] {
        background-color: #131722;
        border-right: 1px solid #1e222d;
    }
    .metric-card {
        background: #1c2030;
        border: 1px solid #1e222d;
        border-radius: 8px;
        padding: 14px 18px;
        margin-bottom: 12px;
    }
    .metric-title {
        font-size: 0.75rem;
        color: #787b86;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .metric-val {
        font-size: 1.5rem;
        font-weight: 700;
        color: #ffffff;
        margin-top: 4px;
    }
    .metric-sub {
        font-size: 0.75rem;
        margin-top: 2px;
    }
    .sub-pos { color: #26a69a; font-weight: 600; }
    .sub-neg { color: #ef5350; font-weight: 600; }
    .badge {
        display: inline-block;
        font-size: 0.65rem;
        font-weight: 700;
        padding: 3px 8px;
        border-radius: 4px;
        background: #252a3a;
        color: #787b86;
        text-transform: uppercase;
        margin-right: 6px;
    }
    .news-card {
        background: #1c2030;
        border: 1px solid #1e222d;
        border-radius: 6px;
        padding: 10px 14px;
        margin-bottom: 8px;
        transition: transform 0.15s;
    }
    .news-card:hover {
        border-color: #2962ff;
        transform: translateY(-1px);
    }
    .news-title {
        font-size: 0.85rem;
        font-weight: 600;
        color: #d1d4dc;
        text-decoration: none;
    }
    .news-title:hover {
        color: #2962ff;
    }
    .news-meta {
        font-size: 0.7rem;
        color: #787b86;
        margin-top: 4px;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# 2. Stock Universe Preset (Top 100 NSE Stocks)
# ---------------------------------------------------------------------------
NSE_STOCKS = [
    {"symbol": "RELIANCE.NS", "name": "Reliance Industries Limited"},
    {"symbol": "TCS.NS", "name": "Tata Consultancy Services"},
    {"symbol": "HDFCBANK.NS", "name": "HDFC Bank"},
    {"symbol": "INFY.NS", "name": "Infosys"},
    {"symbol": "ICICIBANK.NS", "name": "ICICI Bank"},
    {"symbol": "HINDUNILVR.NS", "name": "Hindustan Unilever"},
    {"symbol": "SBIN.NS", "name": "State Bank of India"},
    {"symbol": "BHARTIARTL.NS", "name": "Bharti Airtel"},
    {"symbol": "ITC.NS", "name": "ITC"},
    {"symbol": "KOTAKBANK.NS", "name": "Kotak Mahindra Bank"},
    {"symbol": "LT.NS", "name": "Larsen & Toubro"},
    {"symbol": "AXISBANK.NS", "name": "Axis Bank"},
    {"symbol": "ASIANPAINT.NS", "name": "Asian Paints"},
    {"symbol": "MARUTI.NS", "name": "Maruti Suzuki"},
    {"symbol": "TITAN.NS", "name": "Titan Company"},
    {"symbol": "SUNPHARMA.NS", "name": "Sun Pharma"},
    {"symbol": "BAJFINANCE.NS", "name": "Bajaj Finance"},
    {"symbol": "WIPRO.NS", "name": "Wipro"},
    {"symbol": "ULTRACEMCO.NS", "name": "UltraTech Cement"},
    {"symbol": "HCLTECH.NS", "name": "HCL Technologies"},
    {"symbol": "TATAMOTORS.NS", "name": "Tata Motors"},
    {"symbol": "TATASTEEL.NS", "name": "Tata Steel"},
    {"symbol": "NTPC.NS", "name": "NTPC"},
    {"symbol": "POWERGRID.NS", "name": "Power Grid Corp"},
    {"symbol": "ONGC.NS", "name": "Oil & Natural Gas Corp"},
    {"symbol": "COALINDIA.NS", "name": "Coal India"},
    {"symbol": "JSWSTEEL.NS", "name": "JSW Steel"},
    {"symbol": "ADANIENT.NS", "name": "Adani Enterprises"},
    {"symbol": "ADANIPORTS.NS", "name": "Adani Ports"},
    {"symbol": "TECHM.NS", "name": "Tech Mahindra"},
    {"symbol": "BAJAJFINSV.NS", "name": "Bajaj Finserv"},
    {"symbol": "NESTLEIND.NS", "name": "Nestle India"},
    {"symbol": "DRREDDY.NS", "name": "Dr. Reddys Laboratories"},
    {"symbol": "CIPLA.NS", "name": "Cipla"},
    {"symbol": "DIVISLAB.NS", "name": "Divis Laboratories"},
    {"symbol": "BRITANNIA.NS", "name": "Britannia Industries"},
    {"symbol": "GRASIM.NS", "name": "Grasim Industries"},
    {"symbol": "HEROMOTOCO.NS", "name": "Hero MotoCorp"},
    {"symbol": "EICHERMOT.NS", "name": "Eicher Motors"},
    {"symbol": "BAJAJ-AUTO.NS", "name": "Bajaj Auto"},
    {"symbol": "INDUSINDBK.NS", "name": "IndusInd Bank"},
    {"symbol": "APOLLOHOSP.NS", "name": "Apollo Hospitals"},
    {"symbol": "SBILIFE.NS", "name": "SBI Life Insurance"},
    {"symbol": "HDFCLIFE.NS", "name": "HDFC Life Insurance"},
    {"symbol": "TATACONSUM.NS", "name": "Tata Consumer Products"},
    {"symbol": "M&M.NS", "name": "Mahindra & Mahindra"},
    {"symbol": "BPCL.NS", "name": "Bharat Petroleum"},
    {"symbol": "HINDALCO.NS", "name": "Hindalco Industries"},
    {"symbol": "UPL.NS", "name": "UPL"},
    {"symbol": "VEDL.NS", "name": "Vedanta"},
    {"symbol": "JIOFIN.NS", "name": "Jio Financial Services"},
    {"symbol": "SWIGGY.NS", "name": "Swiggy"},
    {"symbol": "PAYTM.NS", "name": "One 97 Communications (Paytm)"},
    {"symbol": "NYKAA.NS", "name": "FSN E-Commerce (Nykaa)"},
    {"symbol": "DMART.NS", "name": "Avenue Supermarts (DMart)"},
    {"symbol": "PIDILITIND.NS", "name": "Pidilite Industries"},
    {"symbol": "HAVELLS.NS", "name": "Havells India"},
    {"symbol": "SIEMENS.NS", "name": "Siemens"},
    {"symbol": "ABB.NS", "name": "ABB India"},
    {"symbol": "TRENT.NS", "name": "Trent"},
    {"symbol": "IRCTC.NS", "name": "IRCTC"},
    {"symbol": "HAL.NS", "name": "Hindustan Aeronautics"},
    {"symbol": "BEL.NS", "name": "Bharat Electronics"},
    {"symbol": "BANKBARODA.NS", "name": "Bank of Baroda"},
    {"symbol": "PNB.NS", "name": "Punjab National Bank"},
    {"symbol": "CANBK.NS", "name": "Canara Bank"},
    {"symbol": "IOC.NS", "name": "Indian Oil Corporation"},
    {"symbol": "GAIL.NS", "name": "GAIL India"},
    {"symbol": "SAIL.NS", "name": "Steel Authority of India"},
    {"symbol": "NHPC.NS", "name": "NHPC"},
    {"symbol": "RECLTD.NS", "name": "REC Limited"},
    {"symbol": "PFC.NS", "name": "Power Finance Corporation"},
    {"symbol": "IDEA.NS", "name": "Vodafone Idea"},
    {"symbol": "YESBANK.NS", "name": "Yes Bank"},
    {"symbol": "IDFCFIRSTB.NS", "name": "IDFC First Bank"},
    {"symbol": "DLF.NS", "name": "DLF"},
    {"symbol": "GODREJCP.NS", "name": "Godrej Consumer Products"},
    {"symbol": "DABUR.NS", "name": "Dabur India"},
    {"symbol": "COLPAL.NS", "name": "Colgate-Palmolive India"},
    {"symbol": "MARICO.NS", "name": "Marico"},
    {"symbol": "PAGEIND.NS", "name": "Page Industries"},
    {"symbol": "TVSMOTOR.NS", "name": "TVS Motor Company"},
    {"symbol": "BOSCHLTD.NS", "name": "Bosch"},
    {"symbol": "MOTHERSON.NS", "name": "Motherson Sumi Wiring"},
    {"symbol": "MRF.NS", "name": "MRF"},
    {"symbol": "SHREECEM.NS", "name": "Shree Cement"},
    {"symbol": "AMBUJACEM.NS", "name": "Ambuja Cements"},
    {"symbol": "ACC.NS", "name": "ACC"},
    {"symbol": "BERGEPAINT.NS", "name": "Berger Paints"},
    {"symbol": "VOLTAS.NS", "name": "Voltas"},
    {"symbol": "TORNTPHARM.NS", "name": "Torrent Pharma"},
    {"symbol": "LUPIN.NS", "name": "Lupin"},
    {"symbol": "AUROPHARMA.NS", "name": "Aurobindo Pharma"},
    {"symbol": "BIOCON.NS", "name": "Biocon"},
    {"symbol": "MAXHEALTH.NS", "name": "Max Healthcare"},
    {"symbol": "LTIM.NS", "name": "LTIMindtree"},
    {"symbol": "PERSISTENT.NS", "name": "Persistent Systems"},
    {"symbol": "COFORGE.NS", "name": "Coforge"},
    {"symbol": "MPHASIS.NS", "name": "Mphasis"},
    {"symbol": "NAUKRI.NS", "name": "Info Edge (Naukri)"},
    {"symbol": "POLICYBZR.NS", "name": "PB Fintech (PolicyBazaar)"},
]

FACTOR_CONFIG = {
    "usdinr": {"ticker": "USDINR=X", "name": "USD/INR", "color": "#9c27b0", "unit": "₹", "fmt": ".2f"},
    "oil":    {"ticker": "CL=F",     "name": "Crude Oil (WTI)", "color": "#e67e22", "unit": "$", "fmt": ".2f"},
    "gold":   {"ticker": "GC=F",     "name": "Gold (Futures)",  "color": "#ffd700", "unit": "$", "fmt": ".1f"},
    "silver": {"ticker": "SI=F",     "name": "Silver (Futures)","color": "#c0c0c0", "unit": "$", "fmt": ".2f"},
}

# ---------------------------------------------------------------------------
# 3. Cached Data Fetching & Parallel Processing
# ---------------------------------------------------------------------------
@st.cache_data(ttl=1800, show_spinner=False)
def fetch_ticker_data(symbol: str, period: str) -> pd.DataFrame:
    """Fetch and standardize daily historical data for a ticker with automatic fallback."""
    try:
        t = yf.Ticker(symbol)
        df = t.history(period=period, auto_adjust=True)
        if (df is None or df.empty) and period == "max":
            df = t.history(period="10y", auto_adjust=True)
            if df is None or df.empty:
                df = t.history(period="5y", auto_adjust=True)
        if df is None or df.empty:
            return pd.DataFrame()
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df.index = pd.to_datetime(df.index.strftime("%Y-%m-%d"))
        return df.sort_index()
    except Exception as exc:
        return pd.DataFrame()


@st.cache_data(ttl=3600, show_spinner=False)
def get_company_meta(symbol: str) -> dict:
    """Get stock metadata and earnings history."""
    meta = {"name": symbol, "currency": "INR", "sector": "Equities", "industry": "General", "earnings": []}
    try:
        t = yf.Ticker(symbol)
        info = t.info or {}
        meta["name"] = info.get("longName") or info.get("shortName") or symbol
        meta["currency"] = info.get("currency", "INR")
        meta["sector"] = info.get("sector", "Equities")
        meta["industry"] = info.get("industry", "General")

        # Earnings dates
        ed = t.earnings_dates
        if ed is not None and not ed.empty:
            earnings = []
            for dt, row in ed.head(16).iterrows():
                eps_est = row.get("EPS Estimate")
                rep_eps = row.get("Reported EPS")
                surp = row.get("Surprise(%)")
                earnings.append({
                    "date": dt.strftime("%Y-%m-%d"),
                    "epsEstimate": None if pd.isna(eps_est) else round(float(eps_est), 2),
                    "reportedEPS": None if pd.isna(rep_eps) else round(float(rep_eps), 2),
                    "surprisePct": None if pd.isna(surp) else round(float(surp), 2),
                })
            meta["earnings"] = sorted(earnings, key=lambda x: x["date"])
    except Exception:
        pass
    return meta


@st.cache_data(ttl=1800, show_spinner=False)
def load_all_market_data(stock_symbol: str, period: str):
    """Load stock data and macro factors in parallel, aligned to stock trading days."""
    stock_df = fetch_ticker_data(stock_symbol, period)
    if stock_df.empty:
        return None

    meta = get_company_meta(stock_symbol)

    # Parallel factor fetch
    factor_dfs = {}
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {
            pool.submit(fetch_ticker_data, cfg["ticker"], period): fkey
            for fkey, cfg in FACTOR_CONFIG.items()
        }
        for fut in as_completed(futures):
            fkey = futures[fut]
            factor_dfs[fkey] = fut.result()

    # Align factors to stock dates using merge_asof
    aligned_df = pd.DataFrame(index=stock_df.index)
    aligned_df["Stock"] = stock_df["Close"].astype(float)
    aligned_df["Volume"] = stock_df["Volume"].astype(float) if "Volume" in stock_df.columns else 0.0

    for fkey, fdf in factor_dfs.items():
        if not fdf.empty and "Close" in fdf.columns:
            f_close = fdf[["Close"]].copy().sort_index()
            merged = pd.merge_asof(
                pd.DataFrame({"Date": stock_df.index}),
                f_close.reset_index().rename(columns={"index": "Date", "Close": fkey}),
                on="Date",
                direction="backward"
            ).set_index("Date")
            aligned_df[fkey] = merged[fkey].ffill().bfill()
        else:
            aligned_df[fkey] = np.nan

    # Calculate daily percentage returns
    pct_df = aligned_df.pct_change() * 100

    # Calculate overall Pearson correlations
    correlations = {}
    for fkey in FACTOR_CONFIG.keys():
        if fkey in aligned_df.columns and aligned_df[fkey].notna().sum() > 10:
            corr = aligned_df["Stock"].corr(aligned_df[fkey])
            correlations[fkey] = round(float(np.clip(corr, -1.0, 1.0)), 3) if not np.isnan(corr) else 0.0
        else:
            correlations[fkey] = 0.0

    # Rolling 30-day correlations (sampled every 5 days)
    rolling_corr = {}
    for fkey in FACTOR_CONFIG.keys():
        if fkey in aligned_df.columns and aligned_df[fkey].notna().sum() >= 30:
            r = aligned_df["Stock"].rolling(30).corr(aligned_df[fkey]).dropna()
            r = r[~np.isinf(r)]
            sampled = r.iloc[::5]
            rolling_corr[fkey] = sampled.clip(-1.0, 1.0)
        else:
            rolling_corr[fkey] = pd.Series(dtype=float)

    # Multi-factor Ordinary Least Squares (OLS) Elasticity Regression
    # Returns beta: % move in stock per 1% move in factor
    sensitivities = {"usdinr": 0.0, "oil": 0.0, "gold": 0.0, "silver": 0.0, "r2": 0.0}
    try:
        reg_df = aligned_df[["Stock", "usdinr", "oil", "gold", "silver"]].dropna()
        if len(reg_df) >= 30:
            rets = reg_df.pct_change().dropna()
            y = rets["Stock"].values
            X_cols = ["usdinr", "oil", "gold", "silver"]
            X_mat = rets[X_cols].values
            X_with_const = np.column_stack([np.ones(len(y)), X_mat])

            betas, _, _, _ = np.linalg.lstsq(X_with_const, y, rcond=None)
            ss_tot = np.sum((y - np.mean(y)) ** 2)
            ss_res = np.sum((y - (X_with_const @ betas)) ** 2)
            r2_val = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

            sensitivities = {
                "usdinr": round(float(betas[1]), 3),
                "oil": round(float(betas[2]), 3),
                "gold": round(float(betas[3]), 3),
                "silver": round(float(betas[4]), 3),
                "r2": max(0.0, round(float(r2_val), 3)),
            }
    except Exception:
        pass

    # All-Time High & Low
    ath_idx = aligned_df["Stock"].idxmax()
    atl_idx = aligned_df["Stock"].idxmin()

    ath = {
        "date": ath_idx.strftime("%Y-%m-%d"),
        "price": round(float(aligned_df.loc[ath_idx, "Stock"]), 2),
        "factors": {k: round(float(aligned_df.loc[ath_idx, k]), 2) if pd.notna(aligned_df.loc[ath_idx, k]) else None for k in FACTOR_CONFIG.keys()}
    }
    atl = {
        "date": atl_idx.strftime("%Y-%m-%d"),
        "price": round(float(aligned_df.loc[atl_idx, "Stock"]), 2),
        "factors": {k: round(float(aligned_df.loc[atl_idx, k]), 2) if pd.notna(aligned_df.loc[atl_idx, k]) else None for k in FACTOR_CONFIG.keys()}
    }

    return {
        "symbol": stock_symbol,
        "meta": meta,
        "aligned_df": aligned_df,
        "pct_df": pct_df,
        "correlations": correlations,
        "rolling_corr": rolling_corr,
        "sensitivities": sensitivities,
        "ath": ath,
        "atl": atl,
    }


@st.cache_data(ttl=900, show_spinner=False)
def fetch_targeted_news(query: str, date_str: str = "") -> list:
    """Fetch relevant news around a date via Google News RSS."""
    articles = []
    try:
        if date_str:
            target = datetime.strptime(date_str, "%Y-%m-%d")
            start = (target - timedelta(days=4)).strftime("%Y-%m-%d")
            end = (target + timedelta(days=4)).strftime("%Y-%m-%d")
            url = f"https://news.google.com/rss/search?q={requests.utils.quote(query)}+after:{start}+before:{end}&hl=en-IN&gl=IN&ceid=IN:en"
        else:
            url = f"https://news.google.com/rss/search?q={requests.utils.quote(query)}&hl=en-IN&gl=IN&ceid=IN:en"

        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=6)
        if resp.status_code == 200:
            root = ET.fromstring(resp.content)
            for item in root.findall(".//item")[:6]:
                title = item.find("title").text if item.find("title") is not None else ""
                link = item.find("link").text if item.find("link") is not None else "#"
                pub_date = item.find("pubDate").text if item.find("pubDate") is not None else ""
                source_elem = item.find("source")
                source_name = source_elem.text if source_elem is not None else "Google News"
                articles.append({"title": title, "url": link, "source": source_name, "date": pub_date[:16]})
    except Exception:
        pass
    return articles


# ---------------------------------------------------------------------------
# 4. Sidebar Controls & Stock Selection
# ---------------------------------------------------------------------------
st.sidebar.markdown("### 🌐 Stock Correlation Explorer")
st.sidebar.caption("NSE / BSE Multi-Factor Interrelation Dashboard")

# Stock Preset or Custom input
preset_options = [f"{s['symbol']} — {s['name']}" for s in NSE_STOCKS]
selected_preset = st.sidebar.selectbox("Select NSE Benchmark Stock", preset_options, index=0)
selected_symbol_preset = selected_preset.split(" — ")[0]

custom_ticker = st.sidebar.text_input("Or Enter Any Ticker (NSE / BSE)", value="")
active_symbol = custom_ticker.strip().upper() if custom_ticker.strip() else selected_symbol_preset

if not active_symbol.endswith(".NS") and not active_symbol.endswith(".BO"):
    active_symbol += ".NS"

# Timeframe Period Selector
period_choice = st.sidebar.select_slider(
    "Historical Time Horizon",
    options=["1y", "2y", "5y", "10y", "max"],
    value="5y",
    format_func=lambda x: x.upper()
)

st.sidebar.markdown("---")
st.sidebar.markdown("#### ⚙️ Tracked Macro Factors")
show_usd = st.sidebar.checkbox("💱 USD/INR Exchange", value=True)
show_oil = st.sidebar.checkbox("🛢️ Crude Oil (WTI)", value=True)
show_gold = st.sidebar.checkbox("🥇 Gold Futures", value=True)
show_silver = st.sidebar.checkbox("🥈 Silver Futures", value=True)

st.sidebar.markdown("---")
st.sidebar.caption("💡 Data feeds: Yahoo Finance + Google News RSS. Zero API keys required.")


# ---------------------------------------------------------------------------
# 5. Load Data & Display Top Telemetry
# ---------------------------------------------------------------------------
with st.spinner(f"Analyzing multi-factor correlations for {active_symbol}..."):
    data = load_all_market_data(active_symbol, period_choice)

if not data or data["aligned_df"].empty:
    st.error(f"Could not retrieve historical data for `{active_symbol}`. Please verify the ticker symbol.")
    st.stop()

df = data["aligned_df"]
pct = data["pct_df"]
meta = data["meta"]
corrs = data["correlations"]
sens = data["sensitivities"]
ath = data["ath"]
atl = data["atl"]

latest_price = df["Stock"].iloc[-1]
prev_price = df["Stock"].iloc[-2] if len(df) > 1 else latest_price
price_chg = ((latest_price - prev_price) / prev_price) * 100
curr_sym = "₹" if meta["currency"] == "INR" else "$"

# Header Row
col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.title(f"{meta['name']}")
    st.markdown(f"""
        <span class="badge">{active_symbol}</span>
        <span class="badge">{meta['currency']}</span>
        <span class="badge">{meta['sector']}</span>
        <span class="badge">{meta['industry']}</span>
    """, unsafe_allow_html=True)

with col_h2:
    st.markdown(f"""
        <div class="metric-card" style="text-align: right; margin-bottom: 0;">
            <div class="metric-title">Latest Close</div>
            <div class="metric-val">{curr_sym}{latest_price:,.2f}</div>
            <div class="metric-sub {'sub-pos' if price_chg >= 0 else 'sub-neg'}">
                {'+' if price_chg >= 0 else ''}{price_chg:.2f}% (1D)
            </div>
        </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Top Metrics Row: Macro Correlations & Extremes
m_c1, m_c2, m_c3, m_c4, m_c5, m_c6 = st.columns(6)
with m_c1:
    c_val = corrs.get("usdinr", 0)
    st.metric("💱 USD/INR Corr", f"{c_val:+.2f}", "Direct" if c_val >= 0 else "Inverse")
with m_c2:
    c_val = corrs.get("oil", 0)
    st.metric("🛢️ Oil Corr", f"{c_val:+.2f}", "Direct" if c_val >= 0 else "Inverse")
with m_c3:
    c_val = corrs.get("gold", 0)
    st.metric("🥇 Gold Corr", f"{c_val:+.2f}", "Direct" if c_val >= 0 else "Inverse")
with m_c4:
    c_val = corrs.get("silver", 0)
    st.metric("🥈 Silver Corr", f"{c_val:+.2f}", "Direct" if c_val >= 0 else "Inverse")
with m_c5:
    st.metric("🏆 Lifetime High", f"{curr_sym}{ath['price']:,.2f}", ath['date'])
with m_c6:
    st.metric("🔻 Lifetime Low", f"{curr_sym}{atl['price']:,.2f}", atl['date'])

st.markdown("---")


# ---------------------------------------------------------------------------
# 6. Main Interactive Worm Chart (Plotly)
# ---------------------------------------------------------------------------
st.subheader("📈 Interactive Price Worm Graph (Synchronized Macro Tooltip)")
st.caption("Hover along any point on the curve to inspect the exact USD/INR, Gold, Silver, and Oil prices on that identical trading day.")

# Prepare rich customdata for hover: [usdinr, oil, gold, silver, stock_pct, usd_pct, oil_pct, gold_pct, silver_pct]
customdata_matrix = np.column_stack([
    df["usdinr"].fillna(0).values,
    df["oil"].fillna(0).values,
    df["gold"].fillna(0).values,
    df["silver"].fillna(0).values,
    pct["Stock"].fillna(0).values,
    pct["usdinr"].fillna(0).values if "usdinr" in pct.columns else np.zeros(len(df)),
    pct["oil"].fillna(0).values if "oil" in pct.columns else np.zeros(len(df)),
    pct["gold"].fillna(0).values if "gold" in pct.columns else np.zeros(len(df)),
    pct["silver"].fillna(0).values if "silver" in pct.columns else np.zeros(len(df)),
])

hover_template = (
    "<b>📅 %{x|%a, %d %b %Y}</b><br><br>"
    "📈 <b>Stock Price:</b> " + curr_sym + "%{y:,.2f} (%{customdata[4]:+.2f}%)<br>"
    "──────────────────────────<br>"
    "💱 <b>USD/INR:</b> ₹%{customdata[0]:.2f} (%{customdata[5]:+.2f}%)<br>"
    "🛢️ <b>Crude Oil:</b> $%{customdata[1]:.2f}/bbl (%{customdata[6]:+.2f}%)<br>"
    "🥇 <b>Gold:</b> $%{customdata[2]:,.1f}/oz (%{customdata[7]:+.2f}%)<br>"
    "🥈 <b>Silver:</b> $%{customdata[3]:.2f}/oz (%{customdata[8]:+.2f}%)"
    "<extra></extra>"
)

fig_worm = go.Figure()

# Shaded area under the curve
fig_worm.add_trace(go.Scatter(
    x=df.index,
    y=df["Stock"],
    mode="lines",
    name=active_symbol,
    line=dict(color="#2962ff", width=2.2),
    fill="tozeroy",
    fillcolor="rgba(41, 98, 255, 0.08)",
    customdata=customdata_matrix,
    hovertemplate=hover_template,
))

# ATH Pin Annotation
fig_worm.add_annotation(
    x=ath["date"],
    y=ath["price"],
    text=f"🏆 ATH: {curr_sym}{ath['price']:,.2f}",
    showarrow=True,
    arrowhead=2,
    arrowsize=1,
    arrowcolor="#26a69a",
    ax=0,
    ay=-40,
    bgcolor="#1c2030",
    bordercolor="#26a69a",
    font=dict(color="#26a69a", size=11, family="monospace")
)

# ATL Pin Annotation
fig_worm.add_annotation(
    x=atl["date"],
    y=atl["price"],
    text=f"🔻 ATL: {curr_sym}{atl['price']:,.2f}",
    showarrow=True,
    arrowhead=2,
    arrowsize=1,
    arrowcolor="#ef5350",
    ax=0,
    ay=40,
    bgcolor="#1c2030",
    bordercolor="#ef5350",
    font=dict(color="#ef5350", size=11, family="monospace")
)

# Quarterly Earnings Pins (Past 6 Quarters)
earnings_list = meta.get("earnings", [])
stock_dates_set = set(df.index.strftime("%Y-%m-%d"))

for e in earnings_list[-6:]:
    if e["date"] in stock_dates_set:
        stock_price_on_date = df.loc[e["date"], "Stock"]
        surp = e.get("surprisePct")
        beat = surp is not None and surp >= 0
        tag = f"📅 Results ({'+' if beat else ''}{surp:.1f}%)" if surp is not None else "📅 Results"
        fig_worm.add_annotation(
            x=e["date"],
            y=stock_price_on_date,
            text=tag,
            showarrow=True,
            arrowhead=1,
            arrowcolor="#ffca28" if beat else "#ff7043",
            ax=0,
            ay=-25,
            bgcolor="#1c2030",
            bordercolor="#ffca28" if beat else "#ff7043",
            font=dict(color="#ffca28" if beat else "#ff7043", size=9)
        )

fig_worm.update_layout(
    height=480,
    paper_bgcolor="#0a0e17",
    plot_bgcolor="#131722",
    font=dict(color="#d1d4dc"),
    hovermode="x unified",
    margin=dict(l=20, r=20, t=20, b=20),
    xaxis=dict(
        showgrid=True, gridcolor="#1e222d", zeroline=False,
        rangeselector=dict(
            buttons=list([
                dict(count=1, label="1M", step="month", stepmode="backward"),
                dict(count=6, label="6M", step="month", stepmode="backward"),
                dict(count=1, label="1Y", step="year", stepmode="backward"),
                dict(count=5, label="5Y", step="year", stepmode="backward"),
                dict(step="all", label="ALL")
            ]),
            bgcolor="#1c2030",
            font=dict(color="#d1d4dc", size=10)
        ),
        rangeslider=dict(visible=False),
        type="date"
    ),
    yaxis=dict(
        showgrid=True, gridcolor="#1e222d", zeroline=False,
        side="right", tickprefix=curr_sym
    )
)

st.plotly_chart(fig_worm, use_container_width=True)


# ---------------------------------------------------------------------------
# 7. Normalized Factor Overlay & Rolling 30-Day Correlation
# ---------------------------------------------------------------------------
col_chart_left, col_chart_right = st.columns([1, 1])

with col_chart_left:
    st.subheader("🔀 Factor Overlay (Normalized 0–100)")
    st.caption("Visualizes directional coupling and co-trend patterns across all factors.")

    def min_max_norm(s: pd.Series):
        mn, mx = s.min(), s.max()
        if mx <= mn:
            return pd.Series(50.0, index=s.index)
        return ((s - mn) / (mx - mn)) * 100

    fig_norm = go.Figure()
    fig_norm.add_trace(go.Scatter(
        x=df.index, y=min_max_norm(df["Stock"]),
        mode="lines", name=f"{active_symbol} (Stock)",
        line=dict(color="#2962ff", width=2.5)
    ))

    if show_usd and "usdinr" in df.columns:
        fig_norm.add_trace(go.Scatter(
            x=df.index, y=min_max_norm(df["usdinr"]),
            mode="lines", name="USD/INR",
            line=dict(color=FACTOR_CONFIG["usdinr"]["color"], width=1.5)
        ))
    if show_oil and "oil" in df.columns:
        fig_norm.add_trace(go.Scatter(
            x=df.index, y=min_max_norm(df["oil"]),
            mode="lines", name="Crude Oil",
            line=dict(color=FACTOR_CONFIG["oil"]["color"], width=1.5)
        ))
    if show_gold and "gold" in df.columns:
        fig_norm.add_trace(go.Scatter(
            x=df.index, y=min_max_norm(df["gold"]),
            mode="lines", name="Gold",
            line=dict(color=FACTOR_CONFIG["gold"]["color"], width=1.5)
        ))
    if show_silver and "silver" in df.columns:
        fig_norm.add_trace(go.Scatter(
            x=df.index, y=min_max_norm(df["silver"]),
            mode="lines", name="Silver",
            line=dict(color=FACTOR_CONFIG["silver"]["color"], width=1.5)
        ))

    fig_norm.update_layout(
        height=320,
        paper_bgcolor="#0a0e17",
        plot_bgcolor="#131722",
        font=dict(color="#d1d4dc"),
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(showgrid=True, gridcolor="#1e222d"),
        yaxis=dict(showgrid=True, gridcolor="#1e222d", range=[0, 105], side="right"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig_norm, use_container_width=True)

with col_chart_right:
    st.subheader("🔄 Rolling 30-Day Correlation Cycle")
    st.caption("Tracks how factor sensitivity strengthens or flips between market regimes.")

    fig_roll = go.Figure()
    fig_roll.add_hline(y=0, line_dash="dash", line_color="#787b86", line_width=1)

    r_corr = data["rolling_corr"]
    for fkey, cfg in FACTOR_CONFIG.items():
        if fkey in r_corr and not r_corr[fkey].empty:
            fig_roll.add_trace(go.Scatter(
                x=r_corr[fkey].index, y=r_corr[fkey].values,
                mode="lines", name=cfg["name"],
                line=dict(color=cfg["color"], width=1.5)
            ))

    fig_roll.update_layout(
        height=320,
        paper_bgcolor="#0a0e17",
        plot_bgcolor="#131722",
        font=dict(color="#d1d4dc"),
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(showgrid=True, gridcolor="#1e222d"),
        yaxis=dict(showgrid=True, gridcolor="#1e222d", range=[-1.05, 1.05], side="right"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig_roll, use_container_width=True)

st.markdown("---")


# ---------------------------------------------------------------------------
# 8. 🔮 Future What-If Scenario Simulator
# ---------------------------------------------------------------------------
st.subheader("🔮 Future What-If Scenario Simulator")
st.caption("Simulate future shocks to macro factors to predict how this share will react based on historical Ordinary Least Squares (OLS) regression elasticity.")

sim_col1, sim_col2 = st.columns([3, 2])

with sim_col1:
    st.markdown("##### 🎛️ Adjust Macro Factor Shifts (%)")
    
    # Preset triggers
    c_p1, c_p2, c_p3, c_p4 = st.columns(4)
    preset_oil = c_p1.button("🛢️ Oil Shock (+15%)")
    preset_usd = c_p2.button("💱 Rupee Weak (-5%)")
    preset_gold = c_p3.button("🥇 Gold Rally (+10%)")
    preset_rst = c_p4.button("↺ Reset All")

    # Initialize session state for sliders
    if "sim_usd" not in st.session_state or preset_rst:
        st.session_state.sim_usd = 0.0
        st.session_state.sim_oil = 0.0
        st.session_state.sim_gold = 0.0
        st.session_state.sim_silver = 0.0

    if preset_oil:
        st.session_state.sim_oil = 15.0
        st.session_state.sim_usd = 1.5
    if preset_usd:
        st.session_state.sim_usd = 5.0
        st.session_state.sim_gold = 2.0
    if preset_gold:
        st.session_state.sim_gold = 10.0
        st.session_state.sim_silver = 8.0
        st.session_state.sim_oil = -3.0

    val_usd = st.slider("💱 USD/INR Move (%)", -10.0, 10.0, float(st.session_state.sim_usd), 0.5, format="%+.1f%%")
    st.caption(f"Sensitivity Beta: **{sens['usdinr']:+.3f}** (For every 1% USD/INR rise, stock moves {sens['usdinr']:+.2f}%)")

    val_oil = st.slider("🛢️ Crude Oil Move (%)", -25.0, 25.0, float(st.session_state.sim_oil), 1.0, format="%+.1f%%")
    st.caption(f"Sensitivity Beta: **{sens['oil']:+.3f}** (For every 1% Oil rise, stock moves {sens['oil']:+.2f}%)")

    val_gold = st.slider("🥇 Gold Move (%)", -20.0, 20.0, float(st.session_state.sim_gold), 1.0, format="%+.1f%%")
    st.caption(f"Sensitivity Beta: **{sens['gold']:+.3f}**")

    val_silver = st.slider("🥈 Silver Move (%)", -20.0, 20.0, float(st.session_state.sim_silver), 1.0, format="%+.1f%%")
    st.caption(f"Sensitivity Beta: **{sens['silver']:+.3f}**")

with sim_col2:
    st.markdown("##### 🎯 Projected Stock Reaction")
    
    # Calculate impact
    imp_usd = val_usd * sens["usdinr"]
    imp_oil = val_oil * sens["oil"]
    imp_gold = val_gold * sens["gold"]
    imp_silver = val_silver * sens["silver"]
    
    total_delta_pct = imp_usd + imp_oil + imp_gold + imp_silver
    projected_price = latest_price * (1 + total_delta_pct / 100)
    abs_delta = projected_price - latest_price

    delta_color = "sub-pos" if total_delta_pct >= 0 else "sub-neg"
    sign = "+" if total_delta_pct >= 0 else ""

    st.markdown(f"""
        <div class="metric-card" style="border: 2px solid #2962ff; text-align: center; padding: 24px 18px;">
            <div class="metric-title">Expected Future Price</div>
            <div style="font-size: 2.4rem; font-weight: 800; color: #ffffff; margin: 8px 0;">
                {curr_sym}{projected_price:,.2f}
            </div>
            <div style="font-size: 1.2rem;" class="{delta_color}">
                {sign}{total_delta_pct:.2f}% ({sign}{curr_sym}{abs_delta:,.2f})
            </div>
            <hr style="border-color: #1e222d; margin: 16px 0;">
            <div style="text-align: left; font-size: 0.8rem; line-height: 1.8;">
                <div style="display: flex; justify-content: space-between;">
                    <span>USD/INR Impact:</span> <b>{'+' if imp_usd >= 0 else ''}{imp_usd:.2f}%</b>
                </div>
                <div style="display: flex; justify-content: space-between;">
                    <span>Crude Oil Impact:</span> <b>{'+' if imp_oil >= 0 else ''}{imp_oil:.2f}%</b>
                </div>
                <div style="display: flex; justify-content: space-between;">
                    <span>Gold Impact:</span> <b>{'+' if imp_gold >= 0 else ''}{imp_gold:.2f}%</b>
                </div>
                <div style="display: flex; justify-content: space-between;">
                    <span>Silver Impact:</span> <b>{'+' if imp_silver >= 0 else ''}{imp_silver:.2f}%</b>
                </div>
                <div style="display: flex; justify-content: space-between; border-top: 1px dashed #1e222d; margin-top: 6px; padding-top: 6px;">
                    <span>Model Fit (R²):</span> <b>{sens['r2'] * 100:.1f}% explained by macro</b>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

st.markdown("---")


# ---------------------------------------------------------------------------
# 9. Lifetime Extremes, Quarterly Earnings & Targeted News
# ---------------------------------------------------------------------------
tab_ath, tab_earn, tab_news = st.tabs([
    "🏆 Lifetime Extremes (ATH & ATL)",
    "📅 Quarterly Results (Earnings)",
    "📰 Date-Targeted News & Catalysts"
])

with tab_ath:
    col_a1, col_a2 = st.columns(2)
    with col_a1:
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">🏆 All-Time High Context</div>
                <div class="metric-val" style="color: #26a69a;">{curr_sym}{ath['price']:,.2f}</div>
                <div class="metric-sub">Recorded Date: <b>{ath['date']}</b></div>
                <hr style="border-color: #1e222d; margin: 12px 0;">
                <div style="font-size: 0.8rem; line-height: 1.8;">
                    <div>💱 USD/INR: <b>₹{ath['factors']['usdinr'] if ath['factors']['usdinr'] else 'N/A'}</b></div>
                    <div>🛢️ Crude Oil: <b>${ath['factors']['oil'] if ath['factors']['oil'] else 'N/A'}/bbl</b></div>
                    <div>🥇 Gold: <b>${ath['factors']['gold'] if ath['factors']['gold'] else 'N/A'}/oz</b></div>
                    <div>🥈 Silver: <b>${ath['factors']['silver'] if ath['factors']['silver'] else 'N/A'}/oz</b></div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        if st.button("📰 Fetch News around All-Time High Date"):
            st.session_state.news_date_target = ath["date"]

    with col_a2:
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">🔻 All-Time Low Context</div>
                <div class="metric-val" style="color: #ef5350;">{curr_sym}{atl['price']:,.2f}</div>
                <div class="metric-sub">Recorded Date: <b>{atl['date']}</b></div>
                <hr style="border-color: #1e222d; margin: 12px 0;">
                <div style="font-size: 0.8rem; line-height: 1.8;">
                    <div>💱 USD/INR: <b>₹{atl['factors']['usdinr'] if atl['factors']['usdinr'] else 'N/A'}</b></div>
                    <div>🛢️ Crude Oil: <b>${atl['factors']['oil'] if atl['factors']['oil'] else 'N/A'}/bbl</b></div>
                    <div>🥇 Gold: <b>${atl['factors']['gold'] if atl['factors']['gold'] else 'N/A'}/oz</b></div>
                    <div>🥈 Silver: <b>${atl['factors']['silver'] if atl['factors']['silver'] else 'N/A'}/oz</b></div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        if st.button("📰 Fetch News around All-Time Low Date"):
            st.session_state.news_date_target = atl["date"]

with tab_earn:
    st.markdown("##### 📅 Quarterly Financial Results (Reported EPS vs Estimates)")
    if earnings_list:
        earn_records = []
        for e in reversed(earnings_list):
            earn_records.append({
                "Date": e["date"],
                "Reported EPS (₹)": e["reportedEPS"],
                "EPS Estimate (₹)": e["epsEstimate"],
                "Surprise (%)": f"{'+' if (e['surprisePct'] or 0) > 0 else ''}{e['surprisePct']}%" if e['surprisePct'] is not None else "Pending",
                "Outcome": "✅ Beat" if (e['surprisePct'] or 0) >= 0 and e['surprisePct'] is not None else ("❌ Miss" if e['surprisePct'] is not None else "Upcoming")
            })
        st.dataframe(pd.DataFrame(earn_records), use_container_width=True, hide_index=True)
    else:
        st.info("No quarterly financial reports found for this ticker.")

with tab_news:
    target_news_date = st.session_state.get("news_date_target", df.index[-1].strftime("%Y-%m-%d"))
    st.markdown(f"##### 📰 Headlines around `{target_news_date}` for `{meta['name']}`")
    
    with st.spinner("Fetching news..."):
        articles = fetch_targeted_news(meta["name"], target_news_date)

    if articles:
        for art in articles:
            st.markdown(f"""
                <div class="news-card">
                    <a class="news-title" href="{art['url']}" target="_blank">{art['title']}</a>
                    <div class="news-meta">{art['source']} • {art['date']}</div>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.info(f"No major headlines recorded around {target_news_date}.")
