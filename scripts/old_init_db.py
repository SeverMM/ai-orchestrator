# scripts/init_db.py
import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from database.models import Base

async def init_db():
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:password@localhost/ai_orchestrator")
    engine = create_async_engine(DATABASE_URL)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

if __name__ == "__main__":
    asyncio.run(init_db())