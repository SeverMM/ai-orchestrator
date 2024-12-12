import sys
import os
from pathlib import Path

# Add project root to Python path
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

import asyncio
from database.models import Base
from database.connection import engine

async def init_db():
    print("Initializing database...")
    async with engine.begin() as conn:
        print("Dropping all tables...")
        await conn.run_sync(Base.metadata.drop_all)
        print("Creating all tables...")
        await conn.run_sync(Base.metadata.create_all)
        print("Database initialization complete!")

if __name__ == "__main__":
    asyncio.run(init_db())