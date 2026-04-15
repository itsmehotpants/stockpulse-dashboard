"""
GET /api/v1/companies — Returns all tracked companies.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.schemas.stock import CompanyResponse
from app.services import stock_service

router = APIRouter(prefix="/api/v1", tags=["Companies"])


@router.get(
    "/companies",
    response_model=List[CompanyResponse],
    summary="List all companies",
    description="Returns a list of all available companies with their symbol, name, and sector.",
)
def list_companies(db: Session = Depends(get_db)):
    return stock_service.get_all_companies(db)
