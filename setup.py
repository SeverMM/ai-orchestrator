from setuptools import setup, find_packages

setup(
    name="ai_orchestrator",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.104.1",
        "uvicorn>=0.24.0",
        "httpx>=0.25.2",
        "aio-pika>=9.3.0",
        "pydantic>=2.5.2",
        "python-dotenv>=1.0.0",
        "PyYAML>=6.0.1",
        "alembic>=1.7.7",
        "asyncpg>=0.25.0",
        "SQLAlchemy>=1.4.36",
        "psycopg2-binary>=2.9.3"
    ]
)
