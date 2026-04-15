"""
Seed script — downloads stock data, cleans it, and populates the SQLite database.

Usage:
    python -m scripts.seed_data
"""
import sys
import os
import io

# Force UTF-8 output on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Ensure project root is on the path when running as a module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine, SessionLocal, Base
from app.models.stock import Company, StockPrice
from app.data.collector import download_stock_data
from app.data.cleaner import clean_and_transform
from app.config import STOCK_LIST


def seed():
    """Main seeding function."""
    print("=" * 60)
    print("  StockPulse -- Database Seeder")
    print("=" * 60)

    # 1. Create tables
    print("\n[+] Creating database tables ...")
    Base.metadata.create_all(bind=engine)
    print("    Tables created.")

    db = SessionLocal()

    try:
        # 2. Insert companies
        print("\n[+] Inserting companies ...")
        symbol_to_company_id = {}
        for stock_info in STOCK_LIST:
            existing = db.query(Company).filter_by(symbol=stock_info["symbol"]).first()
            if existing:
                symbol_to_company_id[stock_info["symbol"]] = existing.id
                print(f"    SKIP {stock_info['symbol']} already exists (id={existing.id})")
            else:
                company = Company(
                    symbol=stock_info["symbol"],
                    name=stock_info["name"],
                    sector=stock_info["sector"],
                )
                db.add(company)
                db.flush()  # Get the auto-generated id
                symbol_to_company_id[stock_info["symbol"]] = company.id
                print(f"    OK   {stock_info['symbol']} -> id={company.id}")
        db.commit()

        # 3. Download data
        print("\n[+] Downloading stock data from Yahoo Finance ...")
        raw_data = download_stock_data()

        # 4. Clean & transform
        print("\n[+] Cleaning and transforming data ...")
        cleaned_data = clean_and_transform(raw_data)

        # 5. Insert stock prices
        print("\n[+] Inserting stock prices into database ...")
        total_inserted = 0
        for symbol, df in cleaned_data.items():
            company_id = symbol_to_company_id.get(symbol)
            if company_id is None:
                print(f"    WARN No company_id for {symbol}, skipping.")
                continue

            # Delete existing prices for this company (for re-seeding)
            deleted = db.query(StockPrice).filter_by(company_id=company_id).delete()
            if deleted:
                print(f"    DEL  Cleared {deleted} old rows for {symbol}")

            rows = []
            for idx, row in df.iterrows():
                price = StockPrice(
                    company_id=company_id,
                    date=idx.date(),
                    open=round(float(row["Open"]), 2),
                    high=round(float(row["High"]), 2),
                    low=round(float(row["Low"]), 2),
                    close=round(float(row["Close"]), 2),
                    volume=int(row["Volume"]),
                    daily_return=float(row["daily_return"]) if not _is_nan(row["daily_return"]) else None,
                    ma_7=float(row["ma_7"]) if not _is_nan(row["ma_7"]) else None,
                    high_52w=float(row["high_52w"]) if not _is_nan(row["high_52w"]) else None,
                    low_52w=float(row["low_52w"]) if not _is_nan(row["low_52w"]) else None,
                    volatility=float(row["volatility"]) if not _is_nan(row["volatility"]) else None,
                    sentiment_score=float(row["sentiment_score"]) if not _is_nan(row["sentiment_score"]) else None,
                )
                rows.append(price)

            db.bulk_save_objects(rows)
            db.commit()
            total_inserted += len(rows)
            print(f"    OK   {symbol}: {len(rows)} rows inserted")

        print(f"\n[DONE] Seeding complete! Total rows: {total_inserted}")

    except Exception as e:
        db.rollback()
        print(f"\n[ERROR] Seeding failed: {e}")
        raise
    finally:
        db.close()


def _is_nan(value) -> bool:
    """Check if a value is NaN (works for float and numpy types)."""
    try:
        import math
        return math.isnan(float(value))
    except (ValueError, TypeError):
        return True


if __name__ == "__main__":
    seed()
