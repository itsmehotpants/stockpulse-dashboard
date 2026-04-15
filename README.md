# StockPulse — Intelligence Dashboard

**🚀 Live Demo: [https://stockpulse-dashboard-0906.onrender.com/](https://stockpulse-dashboard-0906.onrender.com/)**

A **premium, full-stack financial data intelligence platform** that collects real NSE stock data, applies quantitative analytics, and presents actionable insights through a stunning dark-themed dashboard with professional-grade charts.

![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green?logo=fastapi)
![License](https://img.shields.io/badge/License-MIT-yellow)
![Deployment](https://img.shields.io/badge/Render-Deployed-success?logo=render)

---

## Highlights

| Feature | Description |
|---------|-------------|
| **Market Pulse Dashboard** | Real-time overview: market breadth, sector performance, all-stock cards |
| **Professional Charts** | TradingView candlestick charts with MA overlay + volume histogram |
| **7 Custom Metrics** | Daily Return, 7d MA, 52W Hi/Lo, Volatility Score, Sentiment Index, RSI |
| **AI Price Prediction** | 7-day forecast via Linear Regression with R-squared evaluation |
| **Stock Screener** | Filter by return, volatility, sentiment, and sector |
| **Correlation Heatmap** | Canvas-rendered Pearson correlation matrix across all stocks |
| **Stock Comparison** | Side-by-side normalized performance charts with correlation stats |
| **CSV Export** | Download stock data as CSV for offline analysis |
| **11 REST API Endpoints** | Full Swagger/OpenAPI documentation at `/docs` |
| **Dockerized** | One-command deployment with `docker-compose` |
| **Render-Ready** | `render.yaml` Blueprint for instant cloud deployment |

---

## Architecture

```
+-----------------+     +--------------------+     +------------------+
|  Yahoo Finance  | --> |  Pandas/NumPy      | --> |  SQLite Database |
|  (yfinance API) |     |  (Clean + Metrics) |     |  (2,480 rows)   |
+-----------------+     +--------------------+     +--------+---------+
                                                            |
                                                            v
+------------------+     REST API JSON     +-------------------+
|  Frontend (SPA)  | <------------------- |  FastAPI Backend   |
|  TradingView     |                      |  + ML Prediction   |
|  Charts + Canvas |                      |  + Caching Layer   |
+------------------+                      +-------------------+
```

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.11+ |
| Backend | FastAPI + Uvicorn |
| Database | SQLite + SQLAlchemy ORM |
| Data Source | Yahoo Finance (yfinance) |
| Data Processing | Pandas, NumPy |
| ML (Prediction) | scikit-learn (Linear Regression) |
| Frontend Charts | TradingView Lightweight Charts |
| Heatmap | HTML5 Canvas (custom renderer) |
| Design | Vanilla HTML + CSS + JS (dark theme, glassmorphism) |
| Container | Docker + Docker Compose |
| Deployment | Render (render.yaml Blueprint) |

---

## Quick Start

### Prerequisites
- Python 3.11+

### 1. Clone & Setup
```bash
git clone https://github.com/your-username/stockpulse.git
cd stockpulse
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux
pip install -r requirements.txt
```

### 2. Seed Database
```bash
python -m scripts.seed_data
```
Downloads 1 year of data for 10 NSE stocks and computes all metrics.

### 3. Run
```bash
uvicorn app.main:app --reload
```

### 4. Open
- **Dashboard**: http://localhost:8000
- **Swagger Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## Docker

```bash
docker-compose up --build
```

---

## Cloud Deployment (Render)

1. Push to GitHub
2. Go to [render.com](https://render.com) -> New -> Blueprint
3. Connect your repo — `render.yaml` auto-configures everything
4. Deploy!

---

## API Endpoints (11 total)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/companies` | GET | List all tracked companies |
| `/api/v1/data/{symbol}?days=30` | GET | Stock data for last N days |
| `/api/v1/summary/{symbol}` | GET | 52-week stats + RSI + volatility + sentiment |
| `/api/v1/compare?symbol1=X&symbol2=Y` | GET | Compare two stocks |
| `/api/v1/predict/{symbol}?days=7` | GET | ML price prediction |
| `/api/v1/gainers-losers?n=5` | GET | Top N gainers and losers |
| `/api/v1/market-overview` | GET | Market pulse + sector performance |
| `/api/v1/correlation?days=90` | GET | Correlation matrix of all stocks |
| `/api/v1/screener` | GET | Filter stocks by criteria |
| `/api/v1/export/{symbol}` | GET | Download CSV file |

Full interactive docs at `/docs` (Swagger UI).

---

## Dashboard Features

### 1. Market Overview Tab
- **Market Pulse**: Breadth %, advances/declines, average sentiment
- **Sector Performance**: Color-coded return cards per sector
- **All Stocks at a Glance**: Clickable mini-cards with price, return, volatility

### 2. Stock Detail Tab
- **Professional Candlestick Chart** with 7-day Moving Average overlay
- **Synced Volume Histogram** (green = up day, red = down day)
- **7 Stat Cards**: 52W High, 52W Low, Avg Close, Volatility, Sentiment, Daily Return, RSI
- **Time Range Filters**: 30D / 90D / 6M / 1Y
- **CSV Export**: Download button for offline analysis
- **AI Prediction**: 7-day forecast with R-squared score and dashed prediction line on chart
- **Stock Comparison**: Side-by-side normalized charts + correlation coefficient

### 3. Stock Screener Tab
- Filter by: Min Daily Return %, Max Volatility %, Min Sentiment, Sector
- Results table with sortable columns
- Click any row to view full stock detail

### 4. Correlation Heatmap Tab
- Canvas-rendered color-coded correlation matrix
- Red = negative correlation, Green = positive correlation
- Values shown inside each cell

---

## Stocks Covered (10 NSE)

| Symbol | Company | Sector |
|--------|---------|--------|
| RELIANCE | Reliance Industries | Energy |
| TCS | Tata Consultancy Services | IT Services |
| INFY | Infosys | IT Services |
| HDFCBANK | HDFC Bank | Banking |
| ICICIBANK | ICICI Bank | Banking |
| HINDUNILVR | Hindustan Unilever | FMCG |
| BHARTIARTL | Bharti Airtel | Telecom |
| SBIN | State Bank of India | Banking |
| BAJFINANCE | Bajaj Finance | Financial Services |
| LT | Larsen & Toubro | Engineering |

---

## Custom Analytics

### Daily Return
```
Daily Return = (Close - Open) / Open
```

### 7-Day Moving Average
Rolling mean of closing prices over the last 7 trading days.

### Annualized Volatility
```
Volatility = daily_returns.rolling(30).std() * sqrt(252)
```
Displayed as Low (<15%), Medium (15-30%), or High (>30%).

### RSI (Relative Strength Index)
14-period RSI computed using the standard Wilder smoothing method.
- RSI > 70 = Overbought (red)
- RSI < 30 = Oversold (green)
- 30-70 = Neutral (yellow)

### Mock Sentiment Index (0-100)
Composite score:
- **40%** — Normalized 5-day return
- **30%** — Volume change vs 30-day average
- **30%** — Inverse volatility

Labels: Bullish (70-100) | Neutral (40-70) | Bearish (0-40)

### Pearson Correlation
Pairwise correlation of daily returns between any two stocks. Values near +1 = stocks move together; -1 = inverse.

### ML Price Prediction
- **Model**: Linear Regression (scikit-learn)
- **Features**: Lag-1/2/3 close, 7d MA, lag-1 return, normalized volume
- **Output**: 7-day forecast + R-squared score
- **Disclaimer**: Educational purposes only.

---

## Project Structure

```
Jarnox/
+-- app/
|   +-- main.py              # FastAPI entry point
|   +-- config.py             # Configuration & constants
|   +-- database.py           # SQLAlchemy setup
|   +-- models/stock.py       # ORM models
|   +-- schemas/stock.py      # Pydantic schemas
|   +-- api/routes/            # 4 route files, 11 endpoints
|   +-- services/             # Business logic + ML
|   +-- data/                 # Collector + cleaner
+-- frontend/
|   +-- index.html            # Dashboard (4 tabs)
|   +-- css/styles.css        # Premium dark theme
|   +-- js/                   # App, API, Charts, Utils
+-- scripts/seed_data.py      # Database seeder
+-- requirements.txt
+-- Dockerfile
+-- docker-compose.yml
+-- render.yaml               # Render deployment Blueprint
+-- .gitignore
+-- README.md
```

---

