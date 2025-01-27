import sys
import os
from pathlib import Path

# Add project root to Python path
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

from alembic.config import Config
from alembic import command
import traceback

def test_migration():
    try:
        # Get project root directory
        project_root = Path(__file__).parent.parent
        
        # Create Alembic configuration
        alembic_cfg = Config(str(project_root / "alembic.ini"))
        
        print("Starting test migration...")
        
        # Try to run the migration
        command.upgrade(alembic_cfg, "002_test")
        
        print("Migration successful!")
        
    except Exception as e:
        print(f"Error during migration: {e}")
        print("\nTraceback:")
        traceback.print_exc()

if __name__ == "__main__":
    test_migration()