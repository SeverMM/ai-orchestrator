# scripts/debug_setup.py
import sys
import os
from pathlib import Path

# Add project root to Python path
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

import asyncio
import traceback
from alembic.config import Config
from alembic import command

def debug_alembic_config():
    print("\nChecking Alembic configuration...")
    project_root = Path(__file__).parent.parent
    alembic_ini = project_root / "alembic.ini"
    
    print(f"Alembic.ini path: {alembic_ini}")
    print(f"Exists: {alembic_ini.exists()}")
    
    if alembic_ini.exists():
        with open(alembic_ini, 'r') as f:
            print("\nAlembic.ini contents:")
            print(f.read())

def debug_migrations():
    print("\nChecking migrations...")
    project_root = Path(__file__).parent.parent
    versions_dir = project_root / "migrations" / "versions"
    
    print(f"Versions directory: {versions_dir}")
    print(f"Exists: {versions_dir.exists()}")
    
    if versions_dir.exists():
        print("\nMigration files:")
        for file in versions_dir.glob("*.py"):
            print(f"- {file.name}")
            with open(file, 'r') as f:
                print(f"  First few lines:")
                print("  " + "\n  ".join(f.readlines()[:5]))

def debug_database_connection():
    print("\nChecking database connection...")
    from config.settings import DATABASE_URL
    print(f"Database URL: {DATABASE_URL}")
    
    try:
        import psycopg2
        conn_params = {
            'dbname': 'postgres',
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD'),
            'host': os.getenv('DB_HOST'),
            'port': os.getenv('DB_PORT')
        }
        
        print("\nTrying to connect to PostgreSQL...")
        conn = psycopg2.connect(**conn_params)
        print("Connection successful!")
        conn.close()
    except Exception as e:
        print(f"Connection error: {e}")

async def debug_setup():
    print("Starting debug setup...\n")
    
    print("1. Checking project structure")
    from scripts.check_setup import check_project_structure
    check_project_structure()
    
    print("\n2. Checking Alembic configuration")
    debug_alembic_config()
    
    print("\n3. Checking migrations")
    debug_migrations()
    
    print("\n4. Checking database connection")
    debug_database_connection()
    
    print("\nDebug setup complete!")

if __name__ == "__main__":
    asyncio.run(debug_setup())