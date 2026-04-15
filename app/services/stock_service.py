"""
Stock service — core business logic for querying stock data.
Includes caching for frequently accessed queries.
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, case
from datetime import date, timedelta
from typing import List, Optional, Dict
from functools import lru_cache
import numpy as np

from app.models.stock import Company, StockPrice


def get_all_companies(db: Session) -> List[Company]:
    """Return all tracked companies."""
    return db.query(Company).order_by(Company.symbol).all()


def get_stock_data(
    db: Session,
    symbol: str,
    days: int = 30,
) -> List[StockPrice]:
    """Return the last N days of stock data for a given symbol."""
    company = db.query(Company).filter(Company.symbol == symbol).first()
    if company is None:
        return []

    cutoff = date.today() - timedelta(days=days)

    return (
        db.query(StockPrice)
        .filter(
            StockPrice.company_id == company.id,
            StockPrice.date >= cutoff,
        )
        .order_by(StockPrice.date.asc())
        .all()
    )


def get_summary(db: Session, symbol: str) -> Optional[dict]:
    """Compute 52-week summary statistics for a stock."""
    company = db.query(Company).filter(Company.symbol == symbol).first()
    if company is None:
        return None

    stats = (
        db.query(
            func.max(StockPrice.high_52w).label("high_52w"),
            func.min(StockPrice.low_52w).label("low_52w"),
            func.avg(StockPrice.close).label("avg_close"),
            func.count(StockPrice.id).label("total_records"),
        )
        .filter(StockPrice.company_id == company.id)
        .first()
    )

    latest = (
        db.query(StockPrice)
        .filter(StockPrice.company_id == company.id)
        .order_by(StockPrice.date.desc())
        .first()
    )

    # Compute RSI from last 14 days of close prices
    recent_prices = (
        db.query(StockPrice)
        .filter(StockPrice.company_id == company.id)
        .order_by(StockPrice.date.desc())
        .limit(30)
        .all()
    )
    rsi = _compute_rsi([p.close for p in reversed(recent_prices)])

    return {
        "symbol": company.symbol,
        "name": company.name,
        "sector": company.sector,
        "high_52w": round(stats.high_52w, 2) if stats.high_52w else None,
        "low_52w": round(stats.low_52w, 2) if stats.low_52w else None,
        "avg_close": round(stats.avg_close, 2) if stats.avg_close else None,
        "latest_close": round(latest.close, 2) if latest else None,
        "latest_daily_return": latest.daily_return if latest else None,
        "latest_volatility": latest.volatility if latest else None,
        "latest_sentiment": latest.sentiment_score if latest else None,
        "rsi": rsi,
        "total_records": stats.total_records or 0,
    }


def get_top_gainers_losers(db: Session, n: int = 5) -> dict:
    """Return today's (or latest available day's) top N gainers and losers."""
    latest_date = db.query(func.max(StockPrice.date)).scalar()
    if latest_date is None:
        return {"gainers": [], "losers": []}

    rows = (
        db.query(StockPrice, Company)
        .join(Company, StockPrice.company_id == Company.id)
        .filter(StockPrice.date == latest_date)
        .filter(StockPrice.daily_return.isnot(None))
        .all()
    )

    entries = [
        {
            "symbol": company.symbol,
            "name": company.name,
            "daily_return": round(price.daily_return * 100, 2) if price.daily_return else 0,
            "close": round(price.close, 2),
        }
        for price, company in rows
    ]

    entries.sort(key=lambda x: x["daily_return"], reverse=True)

    return {
        "gainers": entries[:n],
        "losers": list(reversed(entries[-n:])),
        "date": str(latest_date),
    }


def get_market_overview(db: Session) -> dict:
    """
    Returns a comprehensive market overview:
    - Total market cap proxy (sum of latest closes * volume)
    - Sector performance breakdown
    - Market breadth (advances vs declines)
    - Overall market sentiment
    """
    latest_date = db.query(func.max(StockPrice.date)).scalar()
    if latest_date is None:
        return {}

    rows = (
        db.query(StockPrice, Company)
        .join(Company, StockPrice.company_id == Company.id)
        .filter(StockPrice.date == latest_date)
        .all()
    )

    advances = 0
    declines = 0
    sector_data = {}
    total_sentiment = []

    for price, company in rows:
        dr = price.daily_return or 0
        if dr >= 0:
            advances += 1
        else:
            declines += 1

        sector = company.sector
        if sector not in sector_data:
            sector_data[sector] = {"returns": [], "names": []}
        sector_data[sector]["returns"].append(dr * 100)
        sector_data[sector]["names"].append(company.symbol)

        if price.sentiment_score is not None:
            total_sentiment.append(price.sentiment_score)

    # Sector performance
    sectors = []
    for sector_name, data in sector_data.items():
        avg_ret = round(float(np.mean(data["returns"])), 2)
        sectors.append({
            "sector": sector_name,
            "avg_return": avg_ret,
            "stocks": data["names"],
            "count": len(data["returns"]),
        })
    sectors.sort(key=lambda x: x["avg_return"], reverse=True)

    # Market sentiment average
    avg_sentiment = round(float(np.mean(total_sentiment)), 1) if total_sentiment else 50

    return {
        "date": str(latest_date),
        "total_stocks": len(rows),
        "advances": advances,
        "declines": declines,
        "market_breadth": round(advances / max(advances + declines, 1) * 100, 1),
        "avg_sentiment": avg_sentiment,
        "sectors": sectors,
    }


def get_correlation_matrix(db: Session, days: int = 90) -> dict:
    """
    Compute Pearson correlation matrix of daily returns across all stocks.
    Returns a dictionary with symbols and correlation values.
    """
    cutoff = date.today() - timedelta(days=days)
    companies = db.query(Company).order_by(Company.symbol).all()

    # Collect daily returns per stock, indexed by date
    stock_returns = {}
    symbols = []
    for company in companies:
        prices = (
            db.query(StockPrice)
            .filter(StockPrice.company_id == company.id, StockPrice.date >= cutoff)
            .order_by(StockPrice.date.asc())
            .all()
        )
        returns_by_date = {p.date: p.daily_return for p in prices if p.daily_return is not None}
        stock_returns[company.symbol] = returns_by_date
        symbols.append(company.symbol)

    # Find common dates
    all_dates = set()
    for rets in stock_returns.values():
        all_dates.update(rets.keys())
    common_dates = sorted(all_dates)

    # Build return matrix (stocks x days)
    n = len(symbols)
    matrix_data = []
    for sym in symbols:
        row = [stock_returns[sym].get(d) for d in common_dates]
        matrix_data.append(row)

    # Compute correlation matrix
    corr_matrix = []
    for i in range(n):
        row = []
        for j in range(n):
            if i == j:
                row.append(1.0)
            else:
                # Get pairwise valid entries
                pairs = [(matrix_data[i][k], matrix_data[j][k])
                         for k in range(len(common_dates))
                         if matrix_data[i][k] is not None and matrix_data[j][k] is not None]
                if len(pairs) < 5:
                    row.append(None)
                else:
                    r1 = np.array([p[0] for p in pairs])
                    r2 = np.array([p[1] for p in pairs])
                    corr = float(np.corrcoef(r1, r2)[0, 1])
                    row.append(round(corr, 4))
            row_val = row[-1]
        corr_matrix.append(row)

    return {
        "symbols": symbols,
        "matrix": corr_matrix,
    }


def get_screener(db: Session, min_return: Optional[float] = None,
                 max_volatility: Optional[float] = None,
                 min_sentiment: Optional[float] = None,
                 sector: Optional[str] = None) -> list:
    """
    Stock screener: filter companies based on criteria.
    Returns list of stocks matching all provided filters.
    """
    latest_date = db.query(func.max(StockPrice.date)).scalar()
    if not latest_date:
        return []

    rows = (
        db.query(StockPrice, Company)
        .join(Company, StockPrice.company_id == Company.id)
        .filter(StockPrice.date == latest_date)
        .all()
    )

    results = []
    for price, company in rows:
        # Apply filters
        if sector and company.sector.lower() != sector.lower():
            continue
        if min_return is not None and (price.daily_return is None or price.daily_return * 100 < min_return):
            continue
        if max_volatility is not None and (price.volatility is None or price.volatility * 100 > max_volatility):
            continue
        if min_sentiment is not None and (price.sentiment_score is None or price.sentiment_score < min_sentiment):
            continue

        results.append({
            "symbol": company.symbol,
            "name": company.name,
            "sector": company.sector,
            "close": round(price.close, 2),
            "daily_return": round((price.daily_return or 0) * 100, 2),
            "volatility": round((price.volatility or 0) * 100, 2),
            "sentiment_score": round(price.sentiment_score or 0, 1),
            "ma_7": round(price.ma_7, 2) if price.ma_7 else None,
            "high_52w": round(price.high_52w, 2) if price.high_52w else None,
            "low_52w": round(price.low_52w, 2) if price.low_52w else None,
        })

    results.sort(key=lambda x: x["daily_return"], reverse=True)
    return results


def _compute_rsi(closes: list, period: int = 14) -> Optional[float]:
    """Compute Relative Strength Index from a list of close prices."""
    if len(closes) < period + 1:
        return None

    deltas = [closes[i] - closes[i - 1] for i in range(1, len(closes))]
    gains = [d if d > 0 else 0 for d in deltas]
    losses = [-d if d < 0 else 0 for d in deltas]

    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    for i in range(period, len(deltas)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period

    if avg_loss == 0:
        return 100.0

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return round(rsi, 2)
