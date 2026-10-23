# Investment Portfolio Tracker

## Requirements
- Python 3.9 or newer
- No third-party packages are required for sample-price mode.
- Optional live prices: `pip install yfinance`

## Run with sample prices
```bash
python portfolio.py
```

The program asks for a ticker, purchase price per share, and share quantity. Enter
`DONE` at the ticker prompt to finish. It prints a portfolio summary and writes
`portfolio_summary.csv` in the same folder.

## Run with live prices
```bash
pip install yfinance
python portfolio.py --live
```

Live prices depend on data availability and the yfinance service. Prices may be
delayed and should not be treated as guaranteed real-time quotes.

## Calculations
- Invested value = purchase price per share × number of shares
- Market value = current price per share × number of shares
- Profit/loss = market value − invested value
- Percentage return = profit/loss ÷ invested value × 100

## Notes
`sample_prices.csv` contains illustrative example prices only. Replace them with
your own sample data if needed. In live mode, if a quote cannot be retrieved,
the program uses the purchase price for that holding and prints a warning.
The CSV summary is overwritten each time the program runs.
