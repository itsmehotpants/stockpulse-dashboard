"""
Data collector — downloads stock data from Yahoo Finance via yfinance.
"""
import yfinance as yf
import pandas as pd
from typing import Dict, Optional

from app.config import STOCK_LIST, DATA_PERIOD


def download_stock_data(
    symbols: Optional[list] = None,
    period: str = DATA_PERIOD,
) -> Dict[str, pd.DataFrame]:
    """
    Download historical OHLCV data for each stock symbol.

    Args:
        symbols: List of ticker symbols (e.g. ['RELIANCE.NS']).
                 Defaults to all stocks in STOCK_LIST.
        period:  yfinance period string (e.g. '1y', '6mo').

    Returns:
        Dictionary mapping symbol -> DataFrame with columns:
        [Open, High, Low, Close, Volume]
    """
    if symbols is None:
        symbols = [s["symbol"] for s in STOCK_LIST]

    result: Dict[str, pd.DataFrame] = {}

    for symbol in symbols:
        print(f"  [DL] Downloading {symbol} ...")
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period)

            if df.empty:
                print(f"  [WARN] No data returned for {symbol}, skipping.")
                continue

            # Keep only the columns we need
            df = df[["Open", "High", "Low", "Close", "Volume"]].copy()

            # Ensure the index is a DatetimeIndex
            df.index = pd.to_datetime(df.index)

            # Remove timezone info so we can work with plain dates
            if df.index.tz is not None:
                df.index = df.index.tz_localize(None)

            result[symbol] = df
            print(f"  [OK]  {symbol}: {len(df)} rows")

        except Exception as e:
            print(f"  [ERR] Error downloading {symbol}: {e}")

    return result
