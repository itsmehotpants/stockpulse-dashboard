"""
GET /api/v1/compare — Compare two stocks side-by-side.
GET /api/v1/predict/{symbol} — ML price prediction.
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.stock import CompareResponse, PredictionResponse
from app.services import analytics_service, prediction_service

router = APIRouter(prefix="/api/v1", tags=["Analytics"])


@router.get(
    "/compare",
    response_model=CompareResponse,
    summary="Compare two stocks",
    description="Compare two stocks' performance: correlation, returns, and volatility.",
)
def compare_stocks(
    symbol1: str = Query(..., description="First stock symbol"),
    symbol2: str = Query(..., description="Second stock symbol"),
    days: int = Query(90, ge=7, le=365, description="Number of days to compare"),
    db: Session = Depends(get_db),
):
    # Normalize symbols
    if not symbol1.endswith(".NS") and not symbol1.endswith(".BO"):
        symbol1 = symbol1 + ".NS"
    if not symbol2.endswith(".NS") and not symbol2.endswith(".BO"):
        symbol2 = symbol2 + ".NS"

    result = analytics_service.compare_stocks(db, symbol1, symbol2, days)
    if result is None:
        raise HTTPException(status_code=404, detail="One or both symbols not found")
    return result


@router.get(
    "/predict/{symbol}",
    response_model=PredictionResponse,
    summary="Predict stock prices",
    description="Predict future closing prices using a simple Linear Regression model.",
)
def predict_stock(
    symbol: str,
    days: int = Query(7, ge=1, le=30, description="Number of days to forecast"),
    db: Session = Depends(get_db),
):
    if not symbol.endswith(".NS") and not symbol.endswith(".BO"):
        symbol = symbol + ".NS"

    result = prediction_service.predict_prices(db, symbol, days)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Insufficient data for prediction on '{symbol}'")
    return result
