import sys
import os
from pathlib import Path
import asyncio
import subprocess
import time
import psutil
import httpx
from datetime import datetime
from dotenv import load_dotenv

# Add project root to Python path
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

# Load environment variables
load_dotenv()

def log(message: str):
    """Global log function"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")

class ServiceManager:
    def __init__(self):
        self.services = {
            'atlas': {'port': 8000, 'dependencies': []},
            'nova': {'port': 8100, 'dependencies': ['atlas']},
            'sage': {'port': 8200, 'dependencies': ['atlas']},
            'echo': {'port': 8300, 'dependencies': ['nova']},
            'pixel': {'port': 8400, 'dependencies': ['nova']},
            'quantum': {'port': 8500, 'dependencies': ['sage']}
        }
        self.processes = {}
        self.max_retries = 30
        self.retry_delay = 1

    async def check_port(self, port: int) -> bool:
        """Check if a port is in use"""
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('localhost', port))
                s.listen(1)
                s.close()
                return False
            except OSError:
                return True

    async def check_service_health(self, port: int) -> bool:
        """Check if a service is healthy"""
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.get(f"http://localhost:{port}/health")
                return response.status_code == 200
        except Exception:
            return False

    async def start_service(self, name: str) -> bool:
        """Start a single service"""
        service = self.services[name]
        
        # Check dependencies
        for dep in service['dependencies']:
            if not await self.check_service_health(self.services[dep]['port']):
                log(f"Dependency {dep} not ready for {name}")
                return False

        # Check if port is already in use
        if await self.check_port(service['port']):
            log(f"Port {service['port']} is already in use!")
            return False

        try:
            # Start the service
            log(f"Starting {name} service on port {service['port']}...")
            
            service_path = root_dir / 'services' / name / 'service.py'
            process = subprocess.Popen(
                ['python', str(service_path)],
                cwd=str(root_dir),
                env={**os.environ, 'PYTHONPATH': str(root_dir)}
            )
            self.processes[name] = process

            # Wait for service to become healthy
            for attempt in range(self.max_retries):
                if await self.check_service_health(service['port']):
                    log(f"{name.upper()} started successfully")
                    return True
                    
                await asyncio.sleep(self.retry_delay)
                log(f"Waiting for {name} to start (attempt {attempt + 1}/{self.max_retries})...")

            log(f"Failed to start {name} after {self.max_retries} attempts")
            return False

        except Exception as e:
            log(f"Error starting {name}: {e}")
            return False

    async def start_all(self):
        """Start all services in dependency order"""
        log("Starting AI Orchestrator services...")
        
        # Check system dependencies
        try:
            # Check PostgreSQL
            log("Checking PostgreSQL...")
            import psycopg2
            conn = psycopg2.connect(
                dbname=os.getenv('DB_NAME'),
                user=os.getenv('DB_USER'),
                password=os.getenv('DB_PASSWORD'),
                host=os.getenv('DB_HOST'),
                port=os.getenv('DB_PORT')
            )
            conn.close()
            log("PostgreSQL is running")

            # Check RabbitMQ
            log("Checking RabbitMQ...")
            import pika
            connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
            connection.close()
            log("RabbitMQ is running")

            # Check LM Studio API
            log("Checking LM Studio API...")
            async with httpx.AsyncClient() as client:
                response = await client.get("http://localhost:1234/v1/models")
                if response.status_code == 200:
                    log("LM Studio API is running")
                else:
                    raise Exception("LM Studio API not responding")

        except Exception as e:
            log(f"System dependency check failed: {e}")
            return

        # Start services in order
        for service in ['atlas', 'nova', 'sage', 'echo', 'pixel', 'quantum']:
            success = await self.start_service(service)
            if not success:
                log(f"Failed to start {service}, stopping startup sequence")
                await self.cleanup()
                return

        log("\nAll services started successfully!")
        log("\nPress Ctrl+C to stop all services")

    async def cleanup(self):
        """Clean up all processes"""
        log("\nStopping all services...")
        for name, process in self.processes.items():
            try:
                process.terminate()
                log(f"Stopped {name}")
            except Exception as e:
                log(f"Error stopping {name}: {e}")

async def main():
    manager = ServiceManager()
    try:
        await manager.start_all()
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        log("\nShutdown requested...")
    finally:
        await manager.cleanup()
        log("Shutdown complete")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log("\nShutdown complete")