# scripts/check_dependencies.py
import sys
from pathlib import Path

def check_dependencies():
    print("Checking Python version:")
    print(f"Python: {sys.version}")
    
    print("\nChecking required packages:")
    packages = [
        'sqlalchemy',
        'alembic',
        'psycopg2',
        'asyncpg',
        'pydantic'
    ]
    
    for package in packages:
        try:
            module = __import__(package)
            print(f"{package}: {module.__version__ if hasattr(module, '__version__') else 'installed'}")
        except ImportError:
            print(f"{package}: NOT INSTALLED")
    
    print("\nChecking SQLAlchemy types:")
    try:
        from sqlalchemy import Float, Integer, String, DateTime, JSON
        print("SQLAlchemy basic types: Available")
    except ImportError as e:
        print(f"SQLAlchemy types error: {e}")
    
    print("\nChecking Alembic components:")
    try:
        from alembic import op
        from alembic.config import Config
        print("Alembic components: Available")
    except ImportError as e:
        print(f"Alembic components error: {e}")
    
    print("\nChecking project structure:")
    root = Path(__file__).parent.parent
    critical_files = [
        'migrations/env.py',
        'migrations/versions/001_initial.py',
        'alembic.ini'
    ]
    
    for file_path in critical_files:
        full_path = root / file_path
        if full_path.exists():
            with open(full_path, 'r') as f:
                first_line = f.readline().strip()
            print(f"{file_path}: EXISTS (First line: {first_line})")
        else:
            print(f"{file_path}: MISSING")

if __name__ == "__main__":
    check_dependencies()