"""Router do resumo financeiro por mês."""
from __future__ import annotations

import datetime
import re

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import services
from app.database import get_db
from app.schemas import SummaryOut

router = APIRouter(prefix="/api/summary", tags=["summary"])

MES_REGEX = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


@router.get("", response_model=SummaryOut, summary="Resumo financeiro do mês")
def get_summary(
    db: Session = Depends(get_db),
    mes: str = Query(
        default_factory=lambda: datetime.date.today().strftime("%Y-%m"),
        description="Mês no formato YYYY-MM (padrão: mês corrente)",
    ),
) -> SummaryOut:
    if not MES_REGEX.match(mes):
        raise HTTPException(status_code=422, detail="mes deve estar no formato YYYY-MM")
    return SummaryOut(**services.build_summary(db, mes))
