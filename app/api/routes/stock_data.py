"""
GET /api/v1/data/{symbol}   — Stock price data
GET /api/v1/gainers-losers  — Top movers
GET /api/v1/market-overview  — Full market overview with sectors
GET /api/v1/correlation      — Correlation matrix
GET /api/v1/screener         — Filter stocks by criteria
GET /api/v1/export/{symbol}  — Download CSV
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import io
import csv

from app.database import get_db
from app.schemas.stock import (
    StockDataResponse, MarketOverviewResponse,
    CorrelationMatrixResponse, ScreenerResult,
)
from app.services import stock_service

router = APIRouter(prefix="/api/v1", tags=["Stock Data"])


@router.get(
    "/data/{symbol}",
    response_model=List[StockDataResponse],
    summary="Get stock data",
    description="Returns the last N days of stock data for a given symbol. Default is 30 days.",
)
def get_stock_data(
    symbol: str,
    days: int = Query(30, ge=1, le=365, description="Number of days of data to return"),
    db: Session = Depends(get_db),
):
    if not symbol.endswith(".NS") and not symbol.endswith(".BO"):
        symbol = symbol + ".NS"
    data = stock_service.get_stock_data(db, symbol, days)
    if not data:
        raise HTTPException(status_code=404, detail=f"No data found for symbol '{symbol}'")
    return data


@router.get(
    "/gainers-losers",
    summary="Top gainers and losers",
    description="Returns the top N gainers and losers based on the most recent trading day.",
)
def get_gainers_losers(
    n: int = Query(5, ge=1, le=10),
    db: Session = Depends(get_db),
):
    return stock_service.get_top_gainers_losers(db, n)


@router.get(
    "/market-overview",
    response_model=MarketOverviewResponse,
    summary="Market overview",
    description="Returns comprehensive market overview: sector performance, market breadth, sentiment.",
)
def get_market_overview(db: Session = Depends(get_db)):
    return stock_service.get_market_overview(db)


@router.get(
    "/correlation",
    response_model=CorrelationMatrixResponse,
    summary="Correlation matrix",
    description="Pearson correlation matrix of daily returns across all stocks.",
)
def get_correlation(
    days: int = Query(90, ge=7, le=365),
    db: Session = Depends(get_db),
):
    return stock_service.get_correlation_matrix(db, days)


@router.get(
    "/screener",
    response_model=List[ScreenerResult],
    summary="Stock screener",
    description="Filter stocks by criteria: min return, max volatility, min sentiment, sector.",
)
def screener(
    min_return: Optional[float] = Query(None, description="Min daily return (%)"),
    max_volatility: Optional[float] = Query(None, description="Max volatility (%)"),
    min_sentiment: Optional[float] = Query(None, description="Min sentiment score (0-100)"),
    sector: Optional[str] = Query(None, description="Filter by sector name"),
    db: Session = Depends(get_db),
):
    return stock_service.get_screener(db, min_return, max_volatility, min_sentiment, sector)


@router.get(
    "/export/{symbol}",
    summary="Export stock data as CSV",
    description="Download stock price data as a CSV file.",
)
def export_csv(
    symbol: str,
    days: int = Query(365, ge=1, le=365),
    db: Session = Depends(get_db),
):
    if not symbol.endswith(".NS") and not symbol.endswith(".BO"):
        symbol = symbol + ".NS"

    data = stock_service.get_stock_data(db, symbol, days)
    if not data:
        raise HTTPException(status_code=404, detail=f"No data found for '{symbol}'")

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Date", "Open", "High", "Low", "Close", "Volume",
        "Daily Return", "7d MA", "52W High", "52W Low",
        "Volatility", "Sentiment Score",
    ])

    for row in data:
        writer.writerow([
            row.date, row.open, row.high, row.low, row.close, row.volume,
            row.daily_return, row.ma_7, row.high_52w, row.low_52w,
            row.volatility, row.sentiment_score,
        ])

    output.seek(0)
    clean_symbol = symbol.replace(".NS", "").replace(".BO", "")
    filename = f"{clean_symbol}_stock_data.csv"

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
