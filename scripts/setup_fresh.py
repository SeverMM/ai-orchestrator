import sys
import os
from pathlib import Path

# Add project root to Python path
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

from scripts.reset_db import reset_database
from scripts.run_migrations import run_migrations
from scripts.configure_alembic import update_alembic_config

def setup_fresh():
    print("Setting up fresh database...")
    
    try:
        print("\n1. Resetting database...")
        reset_database()
        
        print("\n2. Updating Alembic configuration...")
        update_alembic_config()
        
        print("\n3. Running migrations...")
        run_migrations()
        
        print("\nFresh database setup complete!")
    except Exception as e:
        print(f"\nError during setup: {e}")
        raise

if __name__ == "__main__":
    setup_fresh()