# scripts/cleanup_tables.py
import sys
import os
from pathlib import Path

# Add project root to Python path
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

import asyncio
from database.connection import engine
from database.models import Base

async def cleanup_tables():
    print("Dropping all tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    print("All tables dropped.")

if __name__ == "__main__":
    asyncio.run(cleanup_tables())