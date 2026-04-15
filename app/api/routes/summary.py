"""
GET /api/v1/summary/{symbol} — Returns 52-week summary for a stock.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.stock import SummaryResponse
from app.services import stock_service

router = APIRouter(prefix="/api/v1", tags=["Summary"])


@router.get(
    "/summary/{symbol}",
    response_model=SummaryResponse,
    summary="52-week summary",
    description="Returns the 52-week high, low, average close, and latest metrics for a stock.",
)
def get_summary(
    symbol: str,
    db: Session = Depends(get_db),
):
    if not symbol.endswith(".NS") and not symbol.endswith(".BO"):
        symbol = symbol + ".NS"

    result = stock_service.get_summary(db, symbol)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Company '{symbol}' not found")
    return result
