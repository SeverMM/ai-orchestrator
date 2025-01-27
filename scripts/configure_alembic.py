# scripts/configure_alembic.py
import os
from pathlib import Path
from configparser import ConfigParser

def update_alembic_config():
    print("Updating Alembic configuration...")
    
    # Get database URL from environment
    db_url = f"postgresql+asyncpg://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    
    # Load and update alembic.ini
    config = ConfigParser()
    alembic_ini_path = Path(__file__).parent.parent / 'alembic.ini'
    config.read(alembic_ini_path)
    
    # Update database URL
    config.set('alembic', 'sqlalchemy.url', db_url)
    
    # Write updated config
    with open(alembic_ini_path, 'w') as configfile:
        config.write(configfile)
    
    print("Alembic configuration updated successfully")

if __name__ == "__main__":
    update_alembic_config()