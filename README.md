# AI Orchestrator

An AI orchestration system that coordinates multiple specialized AI agents for comprehensive query processing.

## Architecture

The AI Orchestrator implements a hierarchical thinking system with the following structure:

- **Atlas Service**: Central coordinator that delegates to specialized services
  - **Nova Service**: Technical analysis branch that delegates to:
    - **Echo Service**: Pattern recognition specialist
    - **Pixel Service**: Creative visualization specialist
  - **Sage Service**: Philosophical analysis branch that delegates to:
    - **Quantum Service**: Probabilistic reasoning specialist

Each service implements a 4-step thinking process:
1. Analysis - Initial domain-specific assessment
2. Reflection - Deeper consideration of the analysis
3. Critique - Critical examination of thinking
4. Integration - Synthesis of insights

## Key Features

- **Hierarchical Delegation**: Distributes cognitive tasks across specialized services
- **Multi-Step Thinking**: Each service performs multi-stage analysis for deeper insights
- **Context Propagation**: Parent services pass their analysis to child services
- **Rate Limiting**: Smart timing strategy prevents LLM overload
- **Comprehensive Logging**: Detailed tracking of message flow and thinking process

## Getting Started

### Prerequisites

- Python 3.9+
- LM Studio (for local LLM inference)
- RabbitMQ (for message passing between services)

### Running the Services

Use the provided script to start all services:

```bash
# Windows
start_services.bat

# Linux/Mac (run each in a separate terminal)
python -m services.atlas.service
python -m services.nova.service
python -m services.sage.service
python -m services.echo.service
python -m services.pixel.service
python -m services.quantum.service
```

## Documentation

For more detailed information, see:

- [Full Documentation](DOCUMENTATION.md) - Comprehensive system documentation
- [Developer Guide](DEVELOPER_GUIDE.md) - Quick start guide for developers

## Project Structure

- `/services`: Individual AI services
- `/core`: Shared core functionality
- `/database`: Database models and connection
- `/config`: Configuration for services and models

## API Endpoints

Each service exposes:

- **GET /health**: Check if the service is healthy
- **GET /status**: Get service capabilities and status

Atlas additionally provides:

- **POST /query**: Submit a query to the orchestration system
- **GET /status/{correlation_id}**: Check the status of a submitted query

## Recent Improvements

1. **Timing Strategy**: Implemented deliberate delays to prevent LLM overload and create natural thinking flow
2. **Context Enrichment**: Enhanced parent analysis sharing with child services
3. **Error Handling**: Standardized error handling across all services
4. **Code Optimization**: Consolidated common functionality in base classes

## Contributing

Contributions are welcome! See the developer guide for details on how to extend the system.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
