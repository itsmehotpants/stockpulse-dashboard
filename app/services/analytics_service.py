"""
Analytics service — custom metrics like stock comparison and correlation.
"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
import numpy as np

from app.models.stock import Company, StockPrice


def compare_stocks(db: Session, symbol1: str, symbol2: str, days: int = 90) -> Optional[dict]:
    """
    Compare two stocks: daily return correlation, average returns,
    volatility, and cumulative returns.
    """
    from datetime import date, timedelta

    company1 = db.query(Company).filter(Company.symbol == symbol1).first()
    company2 = db.query(Company).filter(Company.symbol == symbol2).first()

    if not company1 or not company2:
        return None

    cutoff = date.today() - timedelta(days=days)

    data1 = (
        db.query(StockPrice)
        .filter(StockPrice.company_id == company1.id, StockPrice.date >= cutoff)
        .order_by(StockPrice.date.asc())
        .all()
    )
    data2 = (
        db.query(StockPrice)
        .filter(StockPrice.company_id == company2.id, StockPrice.date >= cutoff)
        .order_by(StockPrice.date.asc())
        .all()
    )

    if not data1 or not data2:
        return None

    # Build date-aligned arrays of daily returns
    returns1 = {p.date: p.daily_return for p in data1 if p.daily_return is not None}
    returns2 = {p.date: p.daily_return for p in data2 if p.daily_return is not None}

    common_dates = sorted(set(returns1.keys()) & set(returns2.keys()))

    if len(common_dates) < 5:
        correlation = None
    else:
        r1 = np.array([returns1[d] for d in common_dates])
        r2 = np.array([returns2[d] for d in common_dates])
        corr_matrix = np.corrcoef(r1, r2)
        correlation = round(float(corr_matrix[0, 1]), 4)

    # Cumulative return: (last_close / first_close) - 1
    def _cumulative_return(data):
        if len(data) < 2:
            return None
        return round((data[-1].close / data[0].close - 1) * 100, 2)

    # Average daily return
    def _avg_return(data):
        rets = [p.daily_return for p in data if p.daily_return is not None]
        if not rets:
            return None
        return round(float(np.mean(rets)) * 100, 4)

    # Latest volatility
    def _latest_vol(data):
        for p in reversed(data):
            if p.volatility is not None:
                return round(p.volatility * 100, 2)
        return None

    return {
        "symbol1": company1.symbol,
        "symbol2": company2.symbol,
        "name1": company1.name,
        "name2": company2.name,
        "correlation": correlation,
        "avg_return1": _avg_return(data1),
        "avg_return2": _avg_return(data2),
        "volatility1": _latest_vol(data1),
        "volatility2": _latest_vol(data2),
        "cumulative_return1": _cumulative_return(data1),
        "cumulative_return2": _cumulative_return(data2),
        "data1": data1,
        "data2": data2,
    }
