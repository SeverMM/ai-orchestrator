import sys
import os
from pathlib import Path
import asyncio
from typing import List, Dict, Any
import logging

# Add project root to Python path
root_path = Path(__file__).parent
sys.path.append(str(root_path))

# Import services
from services.atlas.service import AtlasService
from core.utils.logging import setup_logger

logger = setup_logger("startup")

async def check_dependencies():
    """Check if required services are running"""
    # Check LM Studio
    import httpx
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:1234/v1/models")
            if response.status_code != 200:
                logger.error("LM Studio is not responding. Please start LM Studio first.")
                return False
    except Exception as e:
        logger.error(f"Cannot connect to LM Studio: {e}")
        return False

    # Check RabbitMQ
    import aio_pika
    try:
        connection = await aio_pika.connect_robust(
            host="localhost",
            port=5672,
            login="guest",
            password="guest"
        )
        await connection.close()
    except Exception as e:
        logger.error(f"Cannot connect to RabbitMQ: {e}")
        return False

    return True

async def main():
    logger.info("Starting AI Orchestrator...")

    # Check dependencies
    if not await check_dependencies():
        return

    # Start Atlas
    atlas = AtlasService()
    try:
        await atlas.start()
    except KeyboardInterrupt:
        logger.info("Shutdown requested...")
    except Exception as e:
        logger.error(f"Error starting Atlas: {e}")
    finally:
        await atlas.cleanup()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutdown complete.")