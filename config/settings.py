import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

# Database settings
DATABASE_URL = f"{os.getenv('DB_TYPE', 'postgresql')}+asyncpg://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

DB_POOL_SETTINGS = {
    'pool_size': int(os.getenv('DB_POOL_SIZE', 5)),
    'max_overflow': int(os.getenv('DB_MAX_OVERFLOW', 10)),
    'pool_timeout': int(os.getenv('DB_POOL_TIMEOUT', 30)),
    'pool_recycle': int(os.getenv('DB_POOL_RECYCLE', 1800))
}

# Update alembic.ini programmatically
def update_alembic_config():
    from configparser import ConfigParser
    config = ConfigParser()
    alembic_ini_path = Path(__file__).parent.parent / 'alembic.ini'
    config.read(alembic_ini_path)
    config.set('alembic', 'sqlalchemy.url', DATABASE_URL)
    with open(alembic_ini_path, 'w') as configfile:
        config.write(configfile)

# System configuration
SYSTEM_CONFIG = {
    'environment': os.getenv('APP_ENV', 'development'),
    'log_level': os.getenv('LOG_LEVEL', 'INFO'),
    'log_format': os.getenv('LOG_FORMAT', 'detailed'),
    'log_to_file': os.getenv('LOG_TO_FILE', 'false').lower() == 'true',
    'log_file_path': os.getenv('LOG_FILE_PATH', 'logs/ai_orchestrator.log'),
    'request_timeout': int(os.getenv('REQUEST_TIMEOUT', 240)),
    'reflection_depth': int(os.getenv('REFLECTION_DEPTH', 2)),
    'max_retries': int(os.getenv('MAX_RETRIES', 3)),
    'enable_metrics': os.getenv('ENABLE_METRICS', 'true').lower() == 'true',
    'metrics_port': int(os.getenv('METRICS_PORT', 9090))
}

# Service ports
SERVICE_PORTS = {
    'atlas': int(os.getenv('ATLAS_PORT', 8000)),
    'nova': int(os.getenv('NOVA_PORT', 8100)),
    'echo': int(os.getenv('ECHO_PORT', 8200)),
    'pixel': int(os.getenv('PIXEL_PORT', 8300)),
    'sage': int(os.getenv('SAGE_PORT', 8400)),
    'quantum': int(os.getenv('QUANTUM_PORT', 8500))
}

# Model configurations
MODEL_SETTINGS = {
    'atlas': os.getenv('ATLAS_MODEL'),
    'nova': os.getenv('NOVA_MODEL'),
    'sage': os.getenv('SAGE_MODEL'),
    'echo': os.getenv('ECHO_MODEL'),
    'pixel': os.getenv('PIXEL_MODEL'),
    'quantum': os.getenv('QUANTUM_MODEL')
}

# RabbitMQ settings
RABBITMQ_CONFIG = {
    'host': os.getenv('RABBITMQ_HOST', 'localhost'),
    'port': int(os.getenv('RABBITMQ_PORT', 5672)),
    'user': os.getenv('RABBITMQ_USER', 'guest'),
    'password': os.getenv('RABBITMQ_PASSWORD', 'guest'),
    'vhost': os.getenv('RABBITMQ_VHOST', '/')
}