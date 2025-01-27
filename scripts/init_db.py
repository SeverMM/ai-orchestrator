import sys
import os
from pathlib import Path

# Add project root to Python path
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

import asyncio
from database.models import Base, get_all_models
from database.connection import engine

async def init_db():
    """Initialize database with all models"""
    print("Initializing database...")
    
    # Get all models to ensure they're registered
    print("Registering models...")
    models = get_all_models()
    print(f"Found {len(models)} models: {[m.__name__ for m in models]}")
    
    async with engine.begin() as conn:
        print("Dropping all tables...")
        await conn.run_sync(Base.metadata.drop_all)
        
        print("Creating all tables...")
        await conn.run_sync(Base.metadata.create_all)
        
        print("Database initialization complete!")

if __name__ == "__main__":
    try:
        asyncio.run(init_db())
    except Exception as e:
        print(f"Error initializing database: {e}")
        sys.exit(1)