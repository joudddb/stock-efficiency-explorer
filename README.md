# Stock Efficiency Explorer

Ranks stocks (S&P 500, Nasdaq-100 and 16 Saudi companies) by growth per unit of risk over the last 12 months.
Prices come from Yahoo Finance each time the app loads (cached for 1 hour).

- growth = (last close - first close) / first close x 100
- risk = average of (high - low) / open x 100
- efficiency = growth / risk

Run locally: `pip install -r requirements.txt` then `streamlit run app.py`
Student project, not investment advice.
