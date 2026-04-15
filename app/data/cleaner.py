"""
Data cleaner — transforms raw OHLCV data into analysis-ready records
with calculated metrics (daily return, moving averages, volatility, sentiment).
"""
import pandas as pd
import numpy as np
from typing import Dict

from app.config import MOVING_AVG_WINDOW, VOLATILITY_WINDOW, TRADING_DAYS_PER_YEAR


def clean_and_transform(raw_data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
    """
    Clean raw OHLCV DataFrames and add computed metrics.

    Transformations applied:
        1. Handle missing values (forward-fill -> back-fill -> drop)
        2. Normalize date column
        3. Daily Return = (Close - Open) / Open
        4. 7-day Moving Average of Close
        5. 52-week rolling High / Low
        6. Annualized 30-day rolling Volatility
        7. Mock Sentiment Index (0-100)

    Args:
        raw_data: Dict mapping symbol -> raw DataFrame.

    Returns:
        Dict mapping symbol -> cleaned DataFrame with extra columns.
    """
    cleaned: Dict[str, pd.DataFrame] = {}

    for symbol, df in raw_data.items():
        print(f"  [CLN] Cleaning {symbol} ...")
        df = df.copy()

        # --- 1. Handle missing values ---
        df.ffill(inplace=True)
        df.bfill(inplace=True)
        df.dropna(inplace=True)

        if df.empty:
            print(f"  [WARN] {symbol} is empty after cleaning, skipping.")
            continue

        # --- 2. Ensure sorted by date ---
        df.sort_index(inplace=True)

        # --- 3. Daily Return ---
        df["daily_return"] = (df["Close"] - df["Open"]) / df["Open"]

        # --- 4. 7-day Moving Average ---
        df["ma_7"] = df["Close"].rolling(window=MOVING_AVG_WINDOW, min_periods=1).mean()

        # --- 5. 52-week High / Low (rolling 252 trading days) ---
        df["high_52w"] = df["High"].rolling(
            window=TRADING_DAYS_PER_YEAR, min_periods=1
        ).max()
        df["low_52w"] = df["Low"].rolling(
            window=TRADING_DAYS_PER_YEAR, min_periods=1
        ).min()

        # --- 6. Annualized 30-day rolling Volatility ---
        daily_pct_change = df["Close"].pct_change()
        df["volatility"] = (
            daily_pct_change
            .rolling(window=VOLATILITY_WINDOW, min_periods=2)
            .std()
            * np.sqrt(TRADING_DAYS_PER_YEAR)
        )

        # --- 7. Mock Sentiment Index (0-100) ---
        df["sentiment_score"] = _compute_sentiment(df)

        # Round floats to 4 decimal places for clean storage
        float_cols = [
            "daily_return", "ma_7", "high_52w", "low_52w",
            "volatility", "sentiment_score",
        ]
        for col in float_cols:
            df[col] = df[col].round(4)

        cleaned[symbol] = df
        print(f"  [OK]  {symbol}: {len(df)} rows after cleaning")

    return cleaned


def _compute_sentiment(df: pd.DataFrame) -> pd.Series:
    """
    Compute a mock Sentiment Index (0-100) as a composite score:
        40% -- Normalized 5-day return (positive = bullish)
        30% -- Normalized volume change vs 30-day average
        30% -- Inverse normalized volatility (low vol = calm)

    All components are min-max normalized to [0, 1] then combined
    and scaled to 0-100.
    """
    # Component 1: 5-day return
    ret_5d = df["Close"].pct_change(periods=5)

    # Component 2: Volume change vs 30-day moving average
    vol_ma_30 = df["Volume"].rolling(window=30, min_periods=1).mean()
    vol_change = (df["Volume"] - vol_ma_30) / vol_ma_30.replace(0, np.nan)

    # Component 3: Inverse volatility (lower = calmer = better sentiment)
    daily_pct = df["Close"].pct_change()
    rolling_vol = daily_pct.rolling(window=30, min_periods=2).std()

    # Min-max normalize each component to [0, 1]
    def _minmax(s: pd.Series) -> pd.Series:
        s_min = s.min()
        s_max = s.max()
        if s_max == s_min:
            return pd.Series(0.5, index=s.index)
        return (s - s_min) / (s_max - s_min)

    norm_ret = _minmax(ret_5d)
    norm_vol_change = _minmax(vol_change)
    norm_inv_volatility = 1 - _minmax(rolling_vol)  # Invert: low vol = high score

    # Composite
    sentiment = (0.4 * norm_ret + 0.3 * norm_vol_change + 0.3 * norm_inv_volatility) * 100

    return sentiment.fillna(50.0)  # Default to neutral for early rows
