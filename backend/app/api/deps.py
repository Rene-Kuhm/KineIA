from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.postgres import get_db
from app.db.qdrant import get_qdrant


async def get_database(db: AsyncSession = Depends(get_db)):
    return db


def get_vector_db():
    return get_qdrant()
