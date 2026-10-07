# Stock Efficiency Explorer

A website that ranks stocks by how much growth they gave for the risk taken over the last 12 months.

**Try it:** https://joud-stock-efficiency-explorer.streamlit.app/

It covers the S&P 500, the Nasdaq-100 and 16 large Saudi companies on Tadawul. You can:

- choose US, Saudi or both markets
- set the minimum growth and the maximum risk you will accept, and see the best stocks that fit
- compare any companies side by side (for example Nvidia and Google)

Prices come from Yahoo Finance when the page loads and are refreshed every 15 minutes. Yahoo's free prices can be delayed.

## How the numbers work

| Measure | How it is worked out |
|---|---|
| Growth % | (last close - first close) / first close x 100, over the last 12 months |
| Risk score | the average of (high - low) / open x 100 each day, so the typical daily price swing |
| Efficiency score | growth / risk |

The risk score is a simple measure, not a full volatility model.

## How it was built

I first built and tested the method in a Databricks notebook with Python (pandas and Plotly): download one year of daily prices for 500+ stocks, work out growth, risk and efficiency, and chart them. Later I rebuilt it as this website with Streamlit, so anyone can set their own limits and compare companies without running code.

## Files

- `app.py`: the website (layout, inputs, charts)
- `core.py`: downloads the prices and does the calculations
- `requirements.txt`: the Python packages the site needs

To run it on your own computer: `pip install -r requirements.txt`, then `streamlit run app.py`.

## Notes

This is a student project and not investment advice. Past performance does not predict future results.
I used AI tools to help write and debug the code. I checked the results myself.
