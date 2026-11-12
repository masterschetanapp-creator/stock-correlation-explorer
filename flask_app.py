"""
Stock Correlation Explorer — Flask Backend
Analyzes correlations between Indian stocks and macro factors
(USD/INR, Gold, Silver, Crude Oil), fetches news & quarterly results,
and provides future scenario simulation.
"""

import time
import threading
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import xml.etree.ElementTree as ET

import numpy as np
import pandas as pd
import requests
import yfinance as yf
from flask import Flask, jsonify, render_template, request
from flask_cors import CORS

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------
app = Flask(__name__, static_folder="static", template_folder="templates")
CORS(app)

# ---------------------------------------------------------------------------
# In-memory cache: key = "SYMBOL|period" -> {"ts": epoch, "data": dict}
# ---------------------------------------------------------------------------
_cache: dict = {}
_cache_lock = threading.Lock()
CACHE_TTL = 1800  # 30 minutes

FACTOR_TICKERS = {
    "usdinr": "USDINR=X",
    "gold": "GC=F",
    "silver": "SI=F",
    "oil": "CL=F",
}

# ---------------------------------------------------------------------------
# Top 100 NSE stocks for autocomplete
# ---------------------------------------------------------------------------
NSE_STOCKS = [
    {"symbol": "RELIANCE.NS", "name": "Reliance Industries"},
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
    {"symbol": "TMCV.NS", "name": "Tata Motors Limited"},
    {"symbol": "TMPV.NS", "name": "Tata Motors Passenger Vehicles"},
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
    {"symbol": "OFSS.NS", "name": "Oracle Financial Services Software"},
    {"symbol": "TATAELXSI.NS", "name": "Tata Elxsi"},
    {"symbol": "PERSISTENT.NS", "name": "Persistent Systems"},
    {"symbol": "COFORGE.NS", "name": "Coforge"},
    {"symbol": "MPHASIS.NS", "name": "Mphasis"},
    {"symbol": "NAUKRI.NS", "name": "Info Edge (Naukri)"},
    {"symbol": "POLICYBZR.NS", "name": "PB Fintech (PolicyBazaar)"},
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_SESSION = requests.Session()
_SESSION.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
})

def _fetch_ticker(symbol: str, period: str) -> pd.DataFrame:
    """Fetch historical daily data for a single ticker with robust fallback and retries."""
    candidates = [symbol]
    if symbol.endswith(".NS"):
        candidates.append(symbol[:-3] + ".BO")
    elif symbol.endswith(".BO"):
        candidates.append(symbol[:-3] + ".NS")

    periods_to_try = [period]
    if period == "max":
        periods_to_try = ["max", "20y", "10y", "5y"]

    for sym in candidates:
        for p in periods_to_try:
            for attempt in range(3):
                try:
                    ticker = yf.Ticker(sym, session=_SESSION)
                    df = ticker.history(period=p, auto_adjust=True)
                    if df is not None and not df.empty:
                        if isinstance(df.columns, pd.MultiIndex):
                            df.columns = df.columns.get_level_values(0)
                        df.index = pd.to_datetime(df.index.strftime("%Y-%m-%d"))
                        return df.sort_index()
                except Exception as exc:
                    time.sleep(0.3)
    return pd.DataFrame()


def _get_stock_info(symbol: str, ticker_obj: yf.Ticker | None = None) -> dict:
    """Return name, currency, and sector from yfinance ticker.info."""
    try:
        ticker = ticker_obj or yf.Ticker(symbol)
        info = ticker.info or {}
        name = info.get("longName") or info.get("shortName") or symbol
        currency = info.get("currency", "INR")
        sector = info.get("sector", "Unknown")
        industry = info.get("industry", "Unknown")
        return {"name": name, "currency": currency, "sector": sector, "industry": industry}
    except Exception:
        return {"name": symbol, "currency": "INR", "sector": "Unknown", "industry": "Unknown"}


def _get_earnings_dates(ticker_obj: yf.Ticker) -> list[dict]:
    """Retrieve historical and upcoming quarterly results dates & EPS."""
    try:
        ed = ticker_obj.earnings_dates
        if ed is None or ed.empty:
            return []
        results = []
        for dt, row in ed.head(16).iterrows():
            d_str = dt.strftime("%Y-%m-%d")
            eps_est = row.get("EPS Estimate")
            rep_eps = row.get("Reported EPS")
            surp = row.get("Surprise(%)")
            results.append({
                "date": d_str,
                "epsEstimate": None if pd.isna(eps_est) else round(float(eps_est), 2),
                "reportedEPS": None if pd.isna(rep_eps) else round(float(rep_eps), 2),
                "surprisePct": None if pd.isna(surp) else round(float(surp), 2),
            })
        results.sort(key=lambda x: x["date"])
        return results
    except Exception as exc:
        app.logger.warning("Failed to fetch earnings dates: %s", exc)
        return []


def _sanitize_for_json(obj):
    """Recursively replace NaN, inf, -inf with None/valid JSON values."""
    if isinstance(obj, (float, np.floating)):
        if np.isnan(obj) or np.isinf(obj):
            return None
        return float(obj)
    elif isinstance(obj, (int, np.integer)):
        return int(obj)
    elif isinstance(obj, dict):
        return {k: _sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_sanitize_for_json(item) for item in obj]
    return obj


def _cache_key(symbol: str, period: str) -> str:
    return f"{symbol.upper()}|{period}"


def _get_cached(key: str):
    with _cache_lock:
        entry = _cache.get(key)
        if entry and (time.time() - entry["ts"]) < CACHE_TTL:
            return entry["data"]
    return None


def _set_cached(key: str, data: dict):
    with _cache_lock:
        _cache[key] = {"ts": time.time(), "data": data}


def _factor_value_at_date(factor_df: pd.DataFrame, target_date) -> float | None:
    """Get the factor close value at (or nearest before) target_date."""
    if factor_df.empty:
        return None
    try:
        loc = factor_df.index.get_indexer([target_date], method="ffill")[0]
        if loc < 0:
            return None
        return round(float(factor_df.iloc[loc]["Close"]), 2)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Core Analysis & Multi-Factor Sensitivity
# ---------------------------------------------------------------------------

def _analyze(symbol: str, period: str) -> dict | None:
    """Run full correlation analysis & factor elasticity regression."""
    ticker_obj = yf.Ticker(symbol)

    # 1. Fetch stock data
    stock_df = ticker_obj.history(period=period, auto_adjust=True)
    if stock_df is None or stock_df.empty:
        return None
    if isinstance(stock_df.columns, pd.MultiIndex):
        stock_df.columns = stock_df.columns.get_level_values(0)
    stock_df.index = pd.to_datetime(stock_df.index.strftime("%Y-%m-%d"))

    # 2. Get stock info & earnings dates in parallel
    info = _get_stock_info(symbol, ticker_obj)
    earnings = _get_earnings_dates(ticker_obj)

    # 3. Fetch factor data in parallel
    factor_dfs: dict[str, pd.DataFrame] = {}
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {
            pool.submit(_fetch_ticker, ticker, period): name
            for name, ticker in FACTOR_TICKERS.items()
        }
        for fut in as_completed(futures):
            factor_name = futures[fut]
            try:
                factor_dfs[factor_name] = fut.result()
            except Exception:
                factor_dfs[factor_name] = pd.DataFrame()

    # 4. Build stock records
    stock_records = []
    for dt, row in stock_df.iterrows():
        stock_records.append({
            "date": dt.strftime("%Y-%m-%d"),
            "open": round(float(row.get("Open", 0)), 2),
            "high": round(float(row.get("High", 0)), 2),
            "low": round(float(row.get("Low", 0)), 2),
            "close": round(float(row.get("Close", 0)), 2),
            "volume": int(row.get("Volume", 0)),
        })

    # 5. Build factor records (aligned to stock dates via merge_asof)
    factor_records: dict[str, list] = {}
    aligned_factors: dict[str, pd.Series] = {}

    stock_dates = stock_df[["Close"]].copy()
    stock_dates = stock_dates.sort_index()

    for fname, fdf in factor_dfs.items():
        if fdf.empty:
            factor_records[fname] = []
            aligned_factors[fname] = pd.Series(dtype=float)
            continue

        fclose = fdf[["Close"]].copy().sort_index()

        merged = pd.merge_asof(
            stock_dates.reset_index().rename(columns={"index": "Date"}),
            fclose.reset_index().rename(columns={"index": "Date", "Close": "FactorClose"}),
            on="Date",
            direction="backward",
        )
        merged = merged.set_index("Date")

        factor_series = merged["FactorClose"].ffill().bfill()
        aligned_factors[fname] = factor_series

        records = []
        for dt, val in factor_series.items():
            if pd.notna(val):
                records.append({
                    "date": dt.strftime("%Y-%m-%d"),
                    "value": round(float(val), 2),
                })
        factor_records[fname] = records

    # 6. All-time high / low with factor snapshots
    if "Close" in stock_df.columns and not stock_df["Close"].dropna().empty:
        ath_idx = stock_df["Close"].idxmax()
        atl_idx = stock_df["Close"].idxmin()

        def _factor_snapshot(dt):
            snap = {}
            for fname, fdf in factor_dfs.items():
                v = _factor_value_at_date(fdf, dt)
                snap[fname] = v
            return snap

        highlights = {
            "allTimeHigh": {
                "date": ath_idx.strftime("%Y-%m-%d"),
                "close": round(float(stock_df.loc[ath_idx, "Close"]), 2),
                "factors": _factor_snapshot(ath_idx),
            },
            "allTimeLow": {
                "date": atl_idx.strftime("%Y-%m-%d"),
                "close": round(float(stock_df.loc[atl_idx, "Close"]), 2),
                "factors": _factor_snapshot(atl_idx),
            },
        }
    else:
        highlights = {"allTimeHigh": None, "allTimeLow": None}

    # 7. Overall Pearson correlations
    stock_close = stock_df["Close"].copy()
    correlations: dict[str, float | None] = {}
    for fname, fseries in aligned_factors.items():
        if fseries.empty:
            correlations[fname] = None
            continue
        combined = pd.DataFrame({"stock": stock_close, "factor": fseries}).dropna()
        if len(combined) < 5:
            correlations[fname] = None
        else:
            corr = combined["stock"].corr(combined["factor"])
            if pd.isna(corr) or np.isnan(corr) or np.isinf(corr):
                correlations[fname] = None
            else:
                correlations[fname] = round(float(np.clip(corr, -1.0, 1.0)), 4)

    # 8. Rolling 30-day correlations (sampled every 5 days)
    rolling_correlations: dict[str, list] = {}
    for fname, fseries in aligned_factors.items():
        if fseries.empty:
            rolling_correlations[fname] = []
            continue
        combined = pd.DataFrame({"stock": stock_close, "factor": fseries}).dropna()
        if len(combined) < 30:
            rolling_correlations[fname] = []
            continue

        rolling = combined["stock"].rolling(window=30).corr(combined["factor"])
        rolling = rolling.dropna()

        sampled = rolling.iloc[::5]
        records = []
        for dt, val in sampled.items():
            if pd.notna(val) and not np.isnan(val) and not np.isinf(val):
                records.append({
                    "date": dt.strftime("%Y-%m-%d"),
                    "value": round(float(np.clip(val, -1.0, 1.0)), 4),
                })
        rolling_correlations[fname] = records

    # 9. Multi-factor Elasticity / Sensitivity (OLS Regression on Returns)
    # stock_return = a + b1*usd_return + b2*gold_return + b3*silver_return + b4*oil_return
    sensitivities = {"usdinr": 0.0, "gold": 0.0, "silver": 0.0, "oil": 0.0, "r2": 0.0}
    try:
        combined_df = pd.DataFrame({
            "stock": stock_close,
            "usdinr": aligned_factors.get("usdinr", pd.Series(dtype=float)),
            "gold": aligned_factors.get("gold", pd.Series(dtype=float)),
            "silver": aligned_factors.get("silver", pd.Series(dtype=float)),
            "oil": aligned_factors.get("oil", pd.Series(dtype=float)),
        }).dropna()

        if len(combined_df) >= 30:
            rets = combined_df.pct_change().dropna()
            y = rets["stock"].values
            X_cols = ["usdinr", "gold", "silver", "oil"]
            X_mat = rets[X_cols].values
            X_with_const = np.column_stack([np.ones(len(y)), X_mat])

            betas, _, _, _ = np.linalg.lstsq(X_with_const, y, rcond=None)
            ss_tot = np.sum((y - np.mean(y)) ** 2)
            ss_res = np.sum((y - (X_with_const @ betas)) ** 2)
            r2_val = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

            sensitivities = {
                "usdinr": round(float(betas[1]), 3),
                "gold": round(float(betas[2]), 3),
                "silver": round(float(betas[3]), 3),
                "oil": round(float(betas[4]), 3),
                "r2": max(0.0, round(float(r2_val), 3)),
            }
    except Exception as exc:
        app.logger.warning("Sensitivity regression failed: %s", exc)

    return _sanitize_for_json({
        "symbol": symbol,
        "name": info["name"],
        "currency": info["currency"],
        "sector": info["sector"],
        "industry": info["industry"],
        "period": period,
        "currentPrice": round(float(stock_df["Close"].iloc[-1]), 2),
        "stock": stock_records,
        "factors": factor_records,
        "highlights": highlights,
        "correlations": correlations,
        "rollingCorrelations": rolling_correlations,
        "sensitivities": sensitivities,
        "earnings": earnings,
    })


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/analyze/<symbol>")
def analyze(symbol: str):
    period = request.args.get("period", "5y")
    valid_periods = {"1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "max"}
    if period not in valid_periods:
        return jsonify({"error": f"Invalid period. Use one of: {', '.join(sorted(valid_periods))}"}), 400

    key = _cache_key(symbol, period)
    cached = _get_cached(key)
    if cached:
        return jsonify(cached)

    result = _analyze(symbol, period)
    if result is None:
        return jsonify({"error": f"Could not fetch data for symbol '{symbol}'. Verify the ticker (e.g. RELIANCE.NS, TCS.NS) and try again."}), 404

    _set_cached(key, result)
    return jsonify(result)


@app.route("/api/news")
def news():
    """Fetch relevant news around a specific date using Google News RSS + fallback."""
    query = request.args.get("q", "").strip()
    date_str = request.args.get("date", "").strip()

    if not query:
        return jsonify({"articles": []})

    articles = []

    # 1. Try Google News RSS feed (fast, accurate, date-targeted)
    try:
        if date_str:
            target = datetime.strptime(date_str, "%Y-%m-%d")
            start = (target - timedelta(days=3)).strftime("%Y-%m-%d")
            end = (target + timedelta(days=3)).strftime("%Y-%m-%d")
            rss_url = f"https://news.google.com/rss/search?q={requests.utils.quote(query)}+after:{start}+before:{end}&hl=en-IN&gl=IN&ceid=IN:en"
        else:
            rss_url = f"https://news.google.com/rss/search?q={requests.utils.quote(query)}&hl=en-IN&gl=IN&ceid=IN:en"

        resp = requests.get(rss_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}, timeout=6)
        if resp.status_code == 200:
            root = ET.fromstring(resp.content)
            for item in root.findall(".//item")[:10]:
                title = item.find("title").text if item.find("title") is not None else ""
                link = item.find("link").text if item.find("link") is not None else ""
                pub_date = item.find("pubDate").text if item.find("pubDate") is not None else ""
                source_elem = item.find("source")
                source_name = source_elem.text if source_elem is not None else "Google News"

                # Parse date string
                d_formatted = pub_date
                try:
                    dt = datetime.strptime(pub_date[:16], "%a, %d %b %Y")
                    d_formatted = dt.strftime("%Y-%m-%d")
                except Exception:
                    pass

                articles.append({
                    "title": title,
                    "url": link,
                    "source": source_name,
                    "date": d_formatted,
                })
    except Exception as exc:
        app.logger.warning("Google News RSS failed: %s", exc)

    # 2. Fallback to general search if date-targeted RSS returned empty
    if not articles:
        try:
            general_url = f"https://news.google.com/rss/search?q={requests.utils.quote(query)}&hl=en-IN&gl=IN&ceid=IN:en"
            resp = requests.get(general_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
            if resp.status_code == 200:
                root = ET.fromstring(resp.content)
                for item in root.findall(".//item")[:6]:
                    articles.append({
                        "title": item.find("title").text if item.find("title") is not None else "",
                        "url": item.find("link").text if item.find("link") is not None else "",
                        "source": "News Feed",
                        "date": item.find("pubDate").text[:16] if item.find("pubDate") is not None else "",
                    })
        except Exception:
            pass

    return jsonify({"articles": articles})


@app.route("/api/suggest")
def suggest():
    q = request.args.get("q", "").strip().upper()
    if not q:
        return jsonify([])

    matches = []
    for stock in NSE_STOCKS:
        sym = stock["symbol"].upper()
        name = stock["name"].upper()
        if q in sym or q in name:
            matches.append(stock)
        if len(matches) >= 10:
            break

    return jsonify(matches)


@app.route("/api/predict", methods=["POST"])
def predict():
    """Predict stock reaction given user-defined changes in macro factors."""
    body = request.get_json(silent=True) or {}
    sensitivities = body.get("sensitivities", {})
    deltas = body.get("deltas", {})  # e.g. {"usdinr": 2.5, "gold": -1.0, "silver": 0.5, "oil": 5.0} (in %)
    current_price = float(body.get("currentPrice", 0))

    usd_delta = float(deltas.get("usdinr", 0))
    gold_delta = float(deltas.get("gold", 0))
    silver_delta = float(deltas.get("silver", 0))
    oil_delta = float(deltas.get("oil", 0))

    usd_beta = float(sensitivities.get("usdinr", 0))
    gold_beta = float(sensitivities.get("gold", 0))
    silver_beta = float(sensitivities.get("silver", 0))
    oil_beta = float(sensitivities.get("oil", 0))

    # Contributions
    c_usd = usd_delta * usd_beta
    c_gold = gold_delta * gold_beta
    c_silver = silver_delta * silver_beta
    c_oil = oil_delta * oil_beta

    total_predicted_chg_pct = c_usd + c_gold + c_silver + c_oil
    new_price = current_price * (1 + total_predicted_chg_pct / 100) if current_price else 0

    return jsonify({
        "totalChangePct": round(total_predicted_chg_pct, 2),
        "predictedPrice": round(new_price, 2),
        "currentPrice": current_price,
        "breakdown": {
            "usdinr": {"inputDelta": usd_delta, "beta": usd_beta, "impact": round(c_usd, 2)},
            "gold": {"inputDelta": gold_delta, "beta": gold_beta, "impact": round(c_gold, 2)},
            "silver": {"inputDelta": silver_delta, "beta": silver_beta, "impact": round(c_silver, 2)},
            "oil": {"inputDelta": oil_delta, "beta": oil_beta, "impact": round(c_oil, 2)},
        },
    })


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5500, debug=False, threaded=True)
