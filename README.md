# AI Orchestrator

A sophisticated AI orchestration system that coordinates multiple specialized AI agents for comprehensive query processing.

## Architecture

- **Atlas Service**: Central coordinator that delegates to specialized services
- **Nova Service**: Technical analysis specialist
- **Echo Service**: Implementation details specialist
- **Sage Service**: Additional perspective provider
- **Pixel Service**: Pattern recognition specialist
- **Quantum Service**: Advanced reasoning specialist

## Getting Started

### Prerequisites

- Node.js 16+ and npm
- Python 3.9+
- NVIDIA GPU with appropriate drivers (for local LLM inference)

### Running the Frontend

1. Install dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm run dev
```

3. Open [http://localhost:3000](http://localhost:3000) in your browser.

### Running the Backend

1. Start the Atlas service:
```bash
python -m services.atlas.service
```

2. Start other services as needed:
```bash
python -m services.nova.service
python -m services.echo.service
python -m services.sage.service
python -m services.pixel.service
python -m services.quantum.service
```

## API Endpoints

- **POST /query**: Submit a query to the orchestration system
- **GET /status/{correlation_id}**: Check the status of a submitted query
- **GET /health**: Check if the service is healthy

## Project Structure

- `/services`: Individual AI services
- `/core`: Shared core functionality
- `/database`: Database models and connection
- `/config`: Configuration for services and models
- `/pages`: Frontend pages
- `/components`: Frontend UI components
- `/styles`: CSS and styling
