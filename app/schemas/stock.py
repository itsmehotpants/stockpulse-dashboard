"""
Pydantic response schemas for the API.
"""
from pydantic import BaseModel
from datetime import date
from typing import List, Optional


class CompanyResponse(BaseModel):
    """Schema for a single company in the list."""
    id: int
    symbol: str
    name: str
    sector: str

    model_config = {"from_attributes": True}


class StockDataResponse(BaseModel):
    """Schema for a single day of stock data."""
    date: date
    open: float
    high: float
    low: float
    close: float
    volume: int
    daily_return: Optional[float] = None
    ma_7: Optional[float] = None
    high_52w: Optional[float] = None
    low_52w: Optional[float] = None
    volatility: Optional[float] = None
    sentiment_score: Optional[float] = None

    model_config = {"from_attributes": True}


class SummaryResponse(BaseModel):
    """Schema for 52-week summary of a stock."""
    symbol: str
    name: str
    sector: str
    high_52w: Optional[float] = None
    low_52w: Optional[float] = None
    avg_close: Optional[float] = None
    latest_close: Optional[float] = None
    latest_daily_return: Optional[float] = None
    latest_volatility: Optional[float] = None
    latest_sentiment: Optional[float] = None
    rsi: Optional[float] = None
    total_records: int = 0


class CompareResponse(BaseModel):
    """Schema for comparing two stocks."""
    symbol1: str
    symbol2: str
    name1: str
    name2: str
    correlation: Optional[float] = None
    avg_return1: Optional[float] = None
    avg_return2: Optional[float] = None
    volatility1: Optional[float] = None
    volatility2: Optional[float] = None
    cumulative_return1: Optional[float] = None
    cumulative_return2: Optional[float] = None
    data1: List[StockDataResponse] = []
    data2: List[StockDataResponse] = []


class PredictionPoint(BaseModel):
    """A single predicted price point."""
    date: date
    predicted_close: float


class PredictionResponse(BaseModel):
    """Schema for ML prediction results."""
    symbol: str
    model_type: str = "Linear Regression"
    r2_score: Optional[float] = None
    predictions: List[PredictionPoint] = []


class GainerLoserResponse(BaseModel):
    """Schema for top gainer/loser entry."""
    symbol: str
    name: str
    daily_return: float
    close: float


class SectorPerformance(BaseModel):
    """Sector-level aggregate performance."""
    sector: str
    avg_return: float
    stocks: List[str]
    count: int


class MarketOverviewResponse(BaseModel):
    """Full market overview with sector breakdown."""
    date: Optional[str] = None
    total_stocks: int = 0
    advances: int = 0
    declines: int = 0
    market_breadth: float = 0
    avg_sentiment: float = 50
    sectors: List[SectorPerformance] = []


class CorrelationMatrixResponse(BaseModel):
    """Correlation matrix of all stocks."""
    symbols: List[str] = []
    matrix: List[List[Optional[float]]] = []


class ScreenerResult(BaseModel):
    """A single stock from the screener."""
    symbol: str
    name: str
    sector: str
    close: float
    daily_return: float
    volatility: float
    sentiment_score: float
    ma_7: Optional[float] = None
    high_52w: Optional[float] = None
    low_52w: Optional[float] = None
