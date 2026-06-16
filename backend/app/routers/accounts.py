"""Router de contas."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import services
from app.database import get_db
from app.schemas import AccountOut

router = APIRouter(prefix="/api/accounts", tags=["accounts"])


@router.get("", response_model=list[AccountOut], summary="Lista todas as contas")
def get_accounts(db: Session = Depends(get_db)) -> list[AccountOut]:
    return services.list_accounts(db)
