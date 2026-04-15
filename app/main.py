"""
StockPulse Intelligence Dashboard — FastAPI Application Entry Point.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from app.config import API_TITLE, API_DESCRIPTION, API_VERSION
from app.database import engine, Base
from app.api.routes import companies, stock_data, summary, compare

# ─── Create tables on import ─────────────────────────────────────────
Base.metadata.create_all(bind=engine)

# ─── FastAPI App ──────────────────────────────────────────────────────
app = FastAPI(
    title=API_TITLE,
    description=API_DESCRIPTION,
    version=API_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ─── CORS ─────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── API Routes ───────────────────────────────────────────────────────
app.include_router(companies.router)
app.include_router(stock_data.router)
app.include_router(summary.router)
app.include_router(compare.router)

# ─── Static Files (Frontend) ─────────────────────────────────────────
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

if FRONTEND_DIR.exists():
    app.mount("/css", StaticFiles(directory=FRONTEND_DIR / "css"), name="css")
    app.mount("/js", StaticFiles(directory=FRONTEND_DIR / "js"), name="js")

    @app.get("/", include_in_schema=False)
    async def serve_frontend():
        """Serve the main dashboard page."""
        return FileResponse(FRONTEND_DIR / "index.html")
