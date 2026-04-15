"""
Application configuration and constants.
"""
import os
from pathlib import Path

# ─── Paths ────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "stock_data.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

# ─── Stock Universe ───────────────────────────────────────────────────
# 10 major NSE stocks across diverse sectors
STOCK_LIST = [
    {"symbol": "RELIANCE.NS",   "name": "Reliance Industries",        "sector": "Energy"},
    {"symbol": "TCS.NS",        "name": "Tata Consultancy Services",   "sector": "IT Services"},
    {"symbol": "INFY.NS",       "name": "Infosys",                     "sector": "IT Services"},
    {"symbol": "HDFCBANK.NS",   "name": "HDFC Bank",                   "sector": "Banking"},
    {"symbol": "ICICIBANK.NS",  "name": "ICICI Bank",                  "sector": "Banking"},
    {"symbol": "HINDUNILVR.NS", "name": "Hindustan Unilever",          "sector": "FMCG"},
    {"symbol": "BHARTIARTL.NS", "name": "Bharti Airtel",               "sector": "Telecom"},
    {"symbol": "SBIN.NS",       "name": "State Bank of India",         "sector": "Banking"},
    {"symbol": "BAJFINANCE.NS", "name": "Bajaj Finance",               "sector": "Financial Services"},
    {"symbol": "LT.NS",         "name": "Larsen & Toubro",             "sector": "Engineering"},
]

# ─── Data Settings ────────────────────────────────────────────────────
DATA_PERIOD = "1y"  # yfinance period string — fetch 1 year of data
MOVING_AVG_WINDOW = 7
VOLATILITY_WINDOW = 30
TRADING_DAYS_PER_YEAR = 252

# ─── API Settings ─────────────────────────────────────────────────────
API_TITLE = "StockPulse Intelligence API"
API_DESCRIPTION = """
🚀 **StockPulse** — A mini financial data intelligence platform.

Provides cleaned NSE stock market data, custom analytics (volatility scoring,
sentiment index, correlation analysis), and optional ML-based price prediction.
"""
API_VERSION = "1.0.0"
