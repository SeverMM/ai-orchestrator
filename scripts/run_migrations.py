import sys
import os
from pathlib import Path

# Add project root to Python path
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

from alembic.config import Config
from alembic import command
import asyncio

async def run_migrations_async():
    try:
        # Get project root directory
        project_root = Path(__file__).parent.parent
        
        # Create Alembic configuration
        alembic_cfg = Config(str(project_root / "alembic.ini"))
        
        # Run the migrations
        command.upgrade(alembic_cfg, "head")
        print("Migrations completed successfully")
    except Exception as e:
        print(f"Error running migrations: {e}")
        raise

def run_migrations():
    """Synchronous wrapper for running migrations"""
    try:
        # Get project root directory
        project_root = Path(__file__).parent.parent
        
        # Create Alembic configuration
        alembic_cfg = Config(str(project_root / "alembic.ini"))
        
        # Run the migrations
        command.upgrade(alembic_cfg, "head")
        print("Migrations completed successfully")
    except Exception as e:
        print(f"Error running migrations: {e}")
        raise

if __name__ == "__main__":
    run_migrations()