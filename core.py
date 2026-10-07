"""Data download and calculations for the Stock Efficiency Explorer.

Same method as the Databricks notebook:
  growth     = (last close - first close) / first close * 100        (last 12 months)
  risk       = average of (high - low) / open * 100                   (average daily price swing)
  efficiency = growth / risk
"""
import io

import pandas as pd
import requests
import yfinance as yf

SAUDI = {
    "2222.SR": "Saudi Aramco", "1120.SR": "Al Rajhi Bank", "7010.SR": "stc",
    "2010.SR": "SABIC", "1180.SR": "Saudi National Bank", "1010.SR": "Riyad Bank",
    "2082.SR": "ACWA Power", "1150.SR": "Alinma Bank", "2280.SR": "Almarai",
    "1211.SR": "Ma'aden", "1060.SR": "Saudi Awwal Bank", "1050.SR": "Banque Saudi Fransi",
    "2020.SR": "SABIC Agri-Nutrients", "5110.SR": "Saudi Electricity",
    "4013.SR": "Dr. Sulaiman Al Habib", "4190.SR": "Jarir Marketplace",
}

# Common names people search for, added next to the official company name
ALIASES = {"GOOGL": "Google", "GOOG": "Google", "META": "Facebook, Instagram",
           "2222": "Aramco", "7010": "STC"}

SP500_URL = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
NASDAQ100_URL = "https://en.wikipedia.org/wiki/Nasdaq-100"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
CHUNK = 120  # tickers per Yahoo request, to avoid being rate-limited


def _read_tables(url):
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return pd.read_html(io.StringIO(r.text))


def get_us_universe():
    """Return {ticker: company name} for the S&P 500 plus the Nasdaq-100."""
    names = {}
    sp = _read_tables(SP500_URL)[0]
    sym = "Symbol" if "Symbol" in sp.columns else sp.columns[0]
    sec = "Security" if "Security" in sp.columns else sp.columns[1]
    for t, n in zip(sp[sym], sp[sec]):
        names[str(t).replace(".", "-")] = str(n)
    try:
        for t in _read_tables(NASDAQ100_URL):
            cols = [str(c) for c in t.columns]
            if "Ticker" in cols and "Company" in cols:
                for tk, n in zip(t["Ticker"], t["Company"]):
                    names.setdefault(str(tk).replace(".", "-"), str(n))
                break
    except Exception:
        pass  # the S&P 500 list alone is still fine
    return names


def download_prices(tickers):
    """Download one year of daily prices. Returns (frame, list of tickers that failed)."""
    frames = []
    for i in range(0, len(tickers), CHUNK):
        part = tickers[i:i + CHUNK]
        try:
            d = yf.download(part, period="1y", interval="1d", group_by="ticker",
                            threads=True, progress=False)
        except Exception:
            continue
        if d is None or d.empty:
            continue
        if not isinstance(d.columns, pd.MultiIndex):  # single ticker came back flat
            d.columns = pd.MultiIndex.from_product([[part[0]], d.columns])
        frames.append(d)
    if not frames:
        raise RuntimeError("Yahoo Finance returned no data. Try again in a few minutes.")
    data = pd.concat(frames, axis=1)
    got = set(data.columns.get_level_values(0))
    return data, [t for t in tickers if t not in got]


def compute_metrics(data, names):
    """Turn raw prices into one row per stock: growth, risk, efficiency."""
    rows = []
    for t in data.columns.get_level_values(0).unique():
        s = data[t].dropna(subset=["Open", "High", "Low", "Close"])
        s = s[s["Open"] > 0].sort_index()
        if len(s) < 10:
            continue
        growth = (s["Close"].iloc[-1] - s["Close"].iloc[0]) / s["Close"].iloc[0] * 100
        risk = ((s["High"] - s["Low"]) / s["Open"]).mean() * 100
        if not (pd.notna(growth) and pd.notna(risk)) or risk <= 0:
            continue
        rows.append({
            "Company": names.get(t, t),
            "Ticker": t.replace(".SR", ""),
            "Market": "Saudi" if t.endswith(".SR") else "US",
            "Growth": round(float(growth), 2),
            "Risk": round(float(risk), 2),
        })
    df = pd.DataFrame(rows)
    if df.empty:
        raise RuntimeError("No stocks had enough price data.")
    df["Efficiency"] = (df["Growth"] / df["Risk"]).round(2)
    return df.sort_values("Efficiency", ascending=False).reset_index(drop=True)


def load_market_data():
    """Full pipeline: tickers -> prices -> metrics. Returns (metrics, failed tickers)."""
    names = get_us_universe()
    names.update(SAUDI)
    tickers = list(names.keys())
    data, failed = download_prices(tickers)
    return compute_metrics(data, names), failed
