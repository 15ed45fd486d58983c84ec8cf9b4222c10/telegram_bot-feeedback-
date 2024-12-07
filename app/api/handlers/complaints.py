# app/api/handlers/complaints.py

from fastapi import APIRouter, HTTPException, Query, Request
from prisma import Prisma
import logging
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

logger = logging.getLogger("api.handlers.complaints")

router = APIRouter()


class ComplaintOut(BaseModel):
    id: int
    userId: int
    description: str
    latitude: Optional[float]
    longitude: Optional[float]
    status: str
    createdAt: datetime  
    class Config:
        orm_mode = True

@router.get("", response_model=List[ComplaintOut])
async def get_complaints(request: Request, limit: int = Query(10, ge=1), skip: int = Query(0, ge=0)):
    """
    Получить список жалоб с пагинацией.

    - **limit**: Количество жалоб для получения (по умолчанию 10)
    - **skip**: Количество жалоб для пропуска (по умолчанию 0)
    """
    try:
        # Получение экземпляра Prisma клиента из состояния приложения
        db: Prisma = request.app.state.db

        complaints = await db.complaint.find_many(
            order={"createdAt": "desc"},
            take=limit,
            skip=skip
        )
        return complaints
    except Exception as e:
        logger.error(f"Ошибка при получении жалоб: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")
