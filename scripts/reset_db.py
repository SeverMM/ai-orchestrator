import sys
import os
from pathlib import Path

# Add project root to Python path
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

import psycopg2
from config.settings import DATABASE_URL

def reset_database():
    conn_params = {
        'dbname': 'postgres',
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
        
        # Terminate all connections to the database
        cursor.execute(f"""
            SELECT pg_terminate_backend(pg_stat_activity.pid)
            FROM pg_stat_activity
            WHERE pg_stat_activity.datname = '{os.getenv('DB_NAME')}'
            AND pid <> pg_backend_pid();
        """)
        
        # Drop database if exists
        cursor.execute(f"DROP DATABASE IF EXISTS {os.getenv('DB_NAME')}")
        print(f"Database {os.getenv('DB_NAME')} dropped if it existed")
        
        # Create fresh database
        cursor.execute(f"CREATE DATABASE {os.getenv('DB_NAME')}")
        print(f"Database {os.getenv('DB_NAME')} created successfully")
            
    except Exception as e:
        print(f"Error resetting database: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    reset_database()