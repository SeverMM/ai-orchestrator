from sqlalchemy.ext.asyncio import create_async_engine
from database.models import Base
from database.config import DATABASE_URL
import asyncio

async def init_db():
    """Initialize the database"""
    engine = create_async_engine(DATABASE_URL)
    
    async with engine.begin() as conn:
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
        
    await engine.dispose()

def initialize_database():
    """Synchronous wrapper for database initialization"""
    asyncio.run(init_db())

if __name__ == "__main__":
    initialize_database() 