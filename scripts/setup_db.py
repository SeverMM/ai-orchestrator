import sys
import os
from pathlib import Path

# Add project root to Python path
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

import asyncio
from scripts.create_db import create_database
from scripts.run_migrations import run_migrations

async def setup_database():
    print("Setting up database...")
    
    print("\n1. Creating database...")
    create_database()
    
    print("\n2. Running migrations...")
    run_migrations()
    
    print("\nDatabase setup complete!")

if __name__ == "__main__":
    asyncio.run(setup_database())