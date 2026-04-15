"""
SQLAlchemy ORM models for companies and stock prices.
"""
from sqlalchemy import (
    Column, Integer, String, Float, Date, DateTime, ForeignKey, UniqueConstraint
)
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class Company(Base):
    """Represents a tracked stock company."""
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    sector = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    prices = relationship("StockPrice", back_populates="company", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Company(symbol='{self.symbol}', name='{self.name}')>"


class StockPrice(Base):
    """Daily stock price record with calculated metrics."""
    __tablename__ = "stock_prices"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    date = Column(Date, nullable=False, index=True)

    # OHLCV data
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Integer, nullable=False)

    # Calculated metrics
    daily_return = Column(Float)       # (close - open) / open
    ma_7 = Column(Float)              # 7-day moving average of close
    high_52w = Column(Float)          # 52-week rolling high
    low_52w = Column(Float)           # 52-week rolling low
    volatility = Column(Float)         # Annualized 30-day rolling volatility
    sentiment_score = Column(Float)    # Mock sentiment index 0-100

    # Relationship
    company = relationship("Company", back_populates="prices")

    # Ensure no duplicate date per company
    __table_args__ = (
        UniqueConstraint("company_id", "date", name="uq_company_date"),
    )

    def __repr__(self):
        return f"<StockPrice(company_id={self.company_id}, date='{self.date}', close={self.close})>"
