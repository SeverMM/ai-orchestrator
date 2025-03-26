import asyncio
from sqlalchemy import text
from database.connection import get_db_session

async def migrate():
    """Add new columns to existing tables"""
    async with get_db_session() as session:
        try:
            # Modify initial_query to be nullable
            await session.execute(
                text("""
                ALTER TABLE conversation_logs 
                ALTER COLUMN initial_query DROP NOT NULL;
                """)
            )
            
            # Add initial_prompt if it doesn't exist (nullable)
            await session.execute(
                text("""
                ALTER TABLE conversation_logs 
                ADD COLUMN IF NOT EXISTS initial_prompt TEXT;
                """)
            )
            
            # Add context to message_logs if it doesn't exist
            await session.execute(
                text("""
                ALTER TABLE message_logs 
                ADD COLUMN IF NOT EXISTS context JSONB DEFAULT '{}'::jsonb;
                """)
            )
            
            # Add processing_details to message_logs if it doesn't exist
            await session.execute(
                text("""
                ALTER TABLE message_logs 
                ADD COLUMN IF NOT EXISTS processing_details JSONB DEFAULT '{}'::jsonb;
                """)
            )
            
            await session.commit()
            print("Migration completed successfully!")
            
        except Exception as e:
            print(f"Error during migration: {e}")
            await session.rollback()
            raise

def run_migration():
    """Run the migration"""
    asyncio.run(migrate())

if __name__ == "__main__":
    run_migration() 