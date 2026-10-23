"""
Investment Portfolio Tracker
----------------------------
Tracks stock holdings, calculates profit/loss, and writes a CSV summary.

Default mode uses sample_prices.csv so the program works without internet.
Optional live mode uses yfinance:
    pip install yfinance
Then run:
    python portfolio.py --live
"""

import argparse
import csv
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PRICE_FILE = BASE_DIR / "sample_prices.csv"
SUMMARY_FILE = BASE_DIR / "portfolio_summary.csv"


def load_sample_prices(path=PRICE_FILE):
    """Load sample market prices from a CSV file."""
    prices = {}
    if not path.exists():
        return prices

    with path.open("r", newline="", encoding="utf-8") as file:
        for row in csv.DictReader(file):
            symbol = row["symbol"].strip().upper()
            prices[symbol] = float(row["current_price"])
    return prices


def get_live_price(symbol):
    """Fetch the latest available price using yfinance (optional dependency)."""
    try:
        import yfinance as yf
    except ImportError as exc:
        raise RuntimeError(
            "Live prices require yfinance. Install it with: pip install yfinance"
        ) from exc

    ticker = yf.Ticker(symbol)
    history = ticker.history(period="5d")
    if history.empty:
        raise ValueError(f"No price data found for ticker '{symbol}'.")
    return float(history["Close"].dropna().iloc[-1])


def prompt_positive_float(prompt):
    while True:
        try:
            value = float(input(prompt).strip())
            if value <= 0:
                print("Enter a number greater than zero.")
                continue
            return value
        except ValueError:
            print("Invalid number. Please try again.")


def prompt_positive_int(prompt):
    while True:
        try:
            value = int(input(prompt).strip())
            if value <= 0:
                print("Enter a whole number greater than zero.")
                continue
            return value
        except ValueError:
            print("Invalid quantity. Enter a whole number.")


def collect_positions():
    """Collect positions from the user into a dictionary keyed by ticker."""
    positions = {}
    print("Enter stock holdings. Type DONE when you have finished.\n")

    while True:
        symbol = input("Ticker symbol (or DONE): ").strip().upper()
        if symbol == "DONE":
            break
        if not symbol or not symbol.replace(".", "").replace("-", "").isalnum():
            print("Ticker symbol must contain letters/numbers (and may include . or -).")
            continue

        buy_price = prompt_positive_float("Purchase price per share: ")
        quantity = prompt_positive_int("Number of shares: ")

        # If a ticker is entered more than once, combine quantities and cost basis.
        if symbol in positions:
            old = positions[symbol]
            total_shares = old["quantity"] + quantity
            total_cost = old["buy_price"] * old["quantity"] + buy_price * quantity
            positions[symbol] = {
                "buy_price": total_cost / total_shares,
                "quantity": total_shares,
            }
        else:
            positions[symbol] = {"buy_price": buy_price, "quantity": quantity}

        print(f"Added {quantity} share(s) of {symbol}.\n")

    return positions


def calculate_summary(positions, prices):
    """Calculate per-holding and portfolio-wide metrics."""
    rows = []
    total_invested = 0.0
    total_market_value = 0.0

    for symbol, holding in positions.items():
        buy_price = holding["buy_price"]
        quantity = holding["quantity"]

        if symbol not in prices:
            print(
                f"Warning: no current price available for {symbol}; "
                "using its purchase price for this summary."
            )
            current_price = buy_price
        else:
            current_price = prices[symbol]

        invested = buy_price * quantity
        market_value = current_price * quantity
        profit_loss = market_value - invested
        percent_change = (profit_loss / invested * 100) if invested else 0.0

        total_invested += invested
        total_market_value += market_value

        rows.append({
            "symbol": symbol,
            "quantity": quantity,
            "buy_price": buy_price,
            "current_price": current_price,
            "invested": invested,
            "market_value": market_value,
            "profit_loss": profit_loss,
            "percent_change": percent_change,
        })

    total_profit_loss = total_market_value - total_invested
    total_percent = (total_profit_loss / total_invested * 100) if total_invested else 0.0

    totals = {
        "total_invested": total_invested,
        "total_market_value": total_market_value,
        "total_profit_loss": total_profit_loss,
        "total_percent": total_percent,
    }
    return rows, totals


def write_csv(rows, totals, path=SUMMARY_FILE):
    """Write the holdings and a portfolio-total row to CSV."""
    fields = [
        "timestamp", "symbol", "quantity", "buy_price", "current_price",
        "invested", "market_value", "profit_loss", "percent_change"
    ]
    timestamp = datetime.now().astimezone().isoformat(timespec="seconds")

    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()

        for row in rows:
            writer.writerow({
                "timestamp": timestamp,
                "symbol": row["symbol"],
                "quantity": row["quantity"],
                "buy_price": f'{row["buy_price"]:.2f}',
                "current_price": f'{row["current_price"]:.2f}',
                "invested": f'{row["invested"]:.2f}',
                "market_value": f'{row["market_value"]:.2f}',
                "profit_loss": f'{row["profit_loss"]:.2f}',
                "percent_change": f'{row["percent_change"]:.2f}',
            })

        writer.writerow({
            "timestamp": timestamp,
            "symbol": "PORTFOLIO_TOTAL",
            "quantity": "",
            "buy_price": "",
            "current_price": "",
            "invested": f'{totals["total_invested"]:.2f}',
            "market_value": f'{totals["total_market_value"]:.2f}',
            "profit_loss": f'{totals["total_profit_loss"]:.2f}',
            "percent_change": f'{totals["total_percent"]:.2f}',
        })


def print_summary(rows, totals):
    print("\n" + "=" * 96)
    print(f'{"TICKER":<10}{"SHARES":>8}{"BUY PRICE":>13}{"CURRENT":>13}'
          f'{"INVESTED":>14}{"VALUE":>14}{"P/L":>13}{"P/L %":>10}')
    print("-" * 96)

    for row in rows:
        print(
            f'{row["symbol"]:<10}{row["quantity"]:>8}'
            f'{row["buy_price"]:>13.2f}{row["current_price"]:>13.2f}'
            f'{row["invested"]:>14.2f}{row["market_value"]:>14.2f}'
            f'{row["profit_loss"]:>13.2f}{row["percent_change"]:>9.2f}%'
        )

    print("-" * 96)
    print(f'Total invested:      {totals["total_invested"]:.2f}')
    print(f'Current market value:{totals["total_market_value"]:>12.2f}')
    print(f'Overall profit/loss: {totals["total_profit_loss"]:>12.2f}')
    print(f'Overall return:      {totals["total_percent"]:>11.2f}%')


def main():
    parser = argparse.ArgumentParser(description="Track your stock investment portfolio.")
    parser.add_argument(
        "--live", action="store_true",
        help="fetch prices from yfinance instead of using sample_prices.csv"
    )
    args = parser.parse_args()

    positions = collect_positions()
    if not positions:
        print("No holdings entered. Nothing to summarize.")
        return

    if args.live:
        prices = {}
        for symbol in positions:
            try:
                prices[symbol] = get_live_price(symbol)
            except (RuntimeError, ValueError, Exception) as error:
                print(f"Could not retrieve live price for {symbol}: {error}")
    else:
        prices = load_sample_prices()

    rows, totals = calculate_summary(positions, prices)
    print_summary(rows, totals)
    write_csv(rows, totals)
    print(f"\nCSV summary saved to: {SUMMARY_FILE}")


if __name__ == "__main__":
    main()
