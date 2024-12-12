import sys
import os
from pathlib import Path

# Add project root to Python path
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

import psycopg2
from config.settings import DATABASE_URL

def create_database():
    # Parse DATABASE_URL to get components
    # Remove asyncpg specific parts and get base connection info
    base_url = DATABASE_URL.replace('+asyncpg', '')
    
    # Connect to default database to create new database
    conn_params = {
        'dbname': 'postgres',  # Connect to default db first
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD'),
        'host': os.getenv('DB_HOST'),
        'port': os.getenv('DB_PORT')
    }

    try:
        # Connect to default database
        conn = psycopg2.connect(**conn_params)
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{os.getenv('DB_NAME')}'")
        exists = cursor.fetchone()
        
        if not exists:
            # Create database
            cursor.execute(f"CREATE DATABASE {os.getenv('DB_NAME')}")
            print(f"Database {os.getenv('DB_NAME')} created successfully")
        else:
            print(f"Database {os.getenv('DB_NAME')} already exists")
            
    except Exception as e:
        print(f"Error creating database: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    create_database()