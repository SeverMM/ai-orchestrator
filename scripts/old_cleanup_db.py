import sys
import os
from pathlib import Path

# Add project root to Python path
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def cleanup_database():
    conn_params = {
        'dbname': 'postgres',  # Connect to default database
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
        
        db_name = os.getenv('DB_NAME')
        
        print(f"Cleaning up database {db_name}...")
        
        # Terminate all connections
        cursor.execute(f"""
            SELECT pg_terminate_backend(pg_stat_activity.pid)
            FROM pg_stat_activity
            WHERE pg_stat_activity.datname = '{db_name}'
            AND pid <> pg_backend_pid();
        """)
        
        # Drop database if exists
        cursor.execute(f"DROP DATABASE IF EXISTS {db_name}")
        print(f"Dropped database {db_name} if it existed")
        
        # Create fresh database
        cursor.execute(f"CREATE DATABASE {db_name}")
        print(f"Created fresh database {db_name}")
        
        # Connect to the new database to clean up any leftover types
        conn.close()
        conn_params['dbname'] = db_name
        conn = psycopg2.connect(**conn_params)
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Drop enum type if exists
        cursor.execute("DROP TYPE IF EXISTS messagetype CASCADE")
        print("Dropped messagetype enum if it existed")
        
        print("Database cleanup complete!")
        
    except Exception as e:
        print(f"Error during cleanup: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    cleanup_database()