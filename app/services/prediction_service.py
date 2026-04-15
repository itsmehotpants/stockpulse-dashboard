"""
Prediction service — simple ML-based stock price prediction using Linear Regression.
"""
from sqlalchemy.orm import Session
from datetime import date, timedelta
import numpy as np
from typing import Optional

from app.models.stock import Company, StockPrice


def predict_prices(db: Session, symbol: str, forecast_days: int = 7) -> Optional[dict]:
    """
    Predict future closing prices using a simple Linear Regression model.

    Features used:
        - 7-day moving average
        - Lagged close prices (t-1, t-2, t-3)
        - Daily return (t-1)
        - Volume (normalized)

    Returns prediction dict or None if insufficient data.
    """
    from sklearn.linear_model import LinearRegression
    from sklearn.metrics import r2_score

    company = db.query(Company).filter(Company.symbol == symbol).first()
    if not company:
        return None

    # Get all available data
    prices = (
        db.query(StockPrice)
        .filter(StockPrice.company_id == company.id)
        .order_by(StockPrice.date.asc())
        .all()
    )

    if len(prices) < 30:
        return None

    # Build feature matrix
    closes = np.array([p.close for p in prices])
    volumes = np.array([float(p.volume) for p in prices])
    ma7_vals = np.array([p.ma_7 if p.ma_7 else p.close for p in prices])
    returns = np.array([p.daily_return if p.daily_return else 0.0 for p in prices])
    dates_list = [p.date for p in prices]

    # Normalize volume
    vol_mean = volumes.mean() if volumes.mean() != 0 else 1
    volumes_norm = volumes / vol_mean

    # Create features with lags
    X = []
    y = []
    for i in range(3, len(closes)):
        features = [
            closes[i - 1],          # lag-1 close
            closes[i - 2],          # lag-2 close
            closes[i - 3],          # lag-3 close
            ma7_vals[i - 1],        # lag-1 MA7
            returns[i - 1],         # lag-1 return
            volumes_norm[i - 1],    # lag-1 volume (normalized)
        ]
        X.append(features)
        y.append(closes[i])

    X = np.array(X)
    y = np.array(y)

    # Train/test split (80/20, preserving time order)
    split_idx = int(len(X) * 0.8)
    X_train, X_test = X[:split_idx], X[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]

    # Fit model
    model = LinearRegression()
    model.fit(X_train, y_train)

    # Evaluate
    y_pred_test = model.predict(X_test)
    r2 = round(float(r2_score(y_test, y_pred_test)), 4) if len(y_test) > 0 else None

    # Forecast future days
    predictions = []
    # Start from the last known values
    last_closes = list(closes[-3:])
    last_ma7 = float(ma7_vals[-1])
    last_return = float(returns[-1])
    last_vol_norm = float(volumes_norm[-1])
    last_date = dates_list[-1]

    for day_offset in range(1, forecast_days + 1):
        feat = np.array([[
            last_closes[-1],
            last_closes[-2],
            last_closes[-3],
            last_ma7,
            last_return,
            last_vol_norm,
        ]])
        predicted_close = float(model.predict(feat)[0])

        # Calculate next date (skip weekends)
        next_date = last_date + timedelta(days=1)
        while next_date.weekday() >= 5:  # 5=Sat, 6=Sun
            next_date += timedelta(days=1)

        predictions.append({
            "date": next_date,
            "predicted_close": round(predicted_close, 2),
        })

        # Update lag values for next iteration
        new_return = (predicted_close - last_closes[-1]) / last_closes[-1] if last_closes[-1] != 0 else 0
        last_closes.append(predicted_close)
        last_closes = last_closes[-3:]
        last_ma7 = np.mean(last_closes)
        last_return = new_return
        last_date = next_date

    return {
        "symbol": company.symbol,
        "model_type": "Linear Regression",
        "r2_score": r2,
        "predictions": predictions,
    }
