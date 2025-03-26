# AI Orchestrator Developer Guide

## Quick Start

1. **Setup Environment**
   ```bash
   git clone https://github.com/your-username/ai-orchestrator.git
   cd ai-orchestrator
   pip install -r requirements.txt
   ```

2. **Start Services (Windows)**
   ```bash
   start_services.bat
   ```

   **Start Services (Linux/Mac)**
   ```bash
   # Start in separate terminal windows
   python -m services.atlas.service
   python -m services.nova.service
   python -m services.sage.service
   python -m services.echo.service
   python -m services.pixel.service
   python -m services.quantum.service
   ```

3. **Test the System**
   ```bash
   curl -X POST http://localhost:8000/query -H "Content-Type: application/json" -d '{"query": "Your test query"}'
   ```

## Project Structure

```
ai-orchestrator/
├── config/                # Configuration files
│   ├── timing.py          # Timing constants
│   ├── models.py          # LLM model configuration
│   └── services.py        # Service definitions
├── core/                  # Core functionality
│   ├── services/          # Base service classes
│   │   ├── base.py        # BaseService class
│   │   └── base_thinking.py # Thinking capabilities
│   ├── messaging/         # Message broker system
│   └── logging/           # Logging system
├── database/              # Database components
│   └── models.py          # Database models
├── services/              # Service implementations
│   ├── atlas/             # Coordinator service
│   ├── nova/              # Technical branch
│   ├── sage/              # Philosophical branch
│   ├── echo/              # Pattern recognition
│   ├── pixel/             # Creative visualization
│   └── quantum/           # Probabilistic reasoning
└── start_services.bat     # Service launcher
```

## Key Concepts

### Service Hierarchy

```
Atlas (Coordinator)
├── Nova (Technical)
│   ├── Echo (Patterns)
│   └── Pixel (Visuals)
└── Sage (Philosophical)
    └── Quantum (Probabilities)
```

### Message Flow

1. User sends query to Atlas
2. Atlas delegates to Nova and Sage
3. Nova delegates to Echo and Pixel
4. Sage delegates to Quantum
5. Leaf services respond back up the chain
6. Atlas synthesizes final response

### Thinking Process (All Services)

1. **analyze()** - Initial domain-specific assessment
2. **reflect()** - Deeper consideration 
3. **critique()** - Critical examination
4. **integrate()** - Synthesize insights

## Common Development Tasks

### Adding a New Service

1. Create a new directory in `services/`
2. Create `service.py` and `prompts.py` files
3. Register service in `config/services.py`
4. Update hierarchical relationships if needed

### Modifying Prompt Templates

Each service has a `prompts.py` file with a class (e.g., `EchoPrompts`) containing prompt templates.

Example from Echo:
```python
def pattern_analysis(self, content: str, nova_analysis: str = None) -> str:
    """Generate prompt for pattern analysis"""
    if nova_analysis:
        return f"""As Echo, I specialize in pattern recognition. I've received the following query:
{content}

Nova's Technical Analysis:
{nova_analysis}

Please provide a detailed pattern analysis, focusing on:
1. Recurring patterns and motifs
2. Structural similarities
3. Pattern hierarchies
4. Emergent behaviors"""
```

### Adjusting Timing Parameters

Modify timing constants in `config/timing.py`:

```python
# Delays between LLM calls to prevent rate limiting/overload
DELAY_BETWEEN_LLM_CALLS = 10  # seconds

# Service synthesis delays
DELAY_BEFORE_SYNTHESIS = 10  # seconds

# Staggered startup delays for leaf services
DELAY_ECHO_STARTUP = 0        # seconds
DELAY_PIXEL_STARTUP = 5       # seconds
DELAY_QUANTUM_STARTUP = 10    # seconds
```

### Debugging Tips

1. **Check Logs**: Each service logs to a service-specific logger
2. **Common Issues**: 
   - Messaging connection issues
   - Incorrect prompt formats
   - Missing context in messages
   - Timing problems between services
3. **Message Inspection**: Use `SystemLogger.get_conversation_messages()` to examine message flow

## API Reference

### BaseService Methods
- `initialize()`: Set up service components
- `process_message(message)`: Handle incoming messages
- `query_model(prompt)`: Call LLM with prompt
- `extract_parent_analysis(message, parent_service_name)`: Extract parent service analysis

### BaseThinkingService Methods
- `analyze(content, conversation_id, correlation_id, context)`: Initial analysis
- `reflect(content, conversation_id, correlation_id, context)`: Deeper reflection 
- `critique(content, conversation_id, correlation_id, context)`: Critical examination
- `integrate(content, conversation_id, correlation_id, context)`: Insight synthesis
- `respond(content, conversation_id, correlation_id, context, destination)`: Send response up chain

## LLM Integration

The system uses Language Model Studio (LM Studio) to run local LLMs. Make sure LM Studio is running locally with the appropriate models loaded:

- Model: Phi-3.1-mini-128k-instruct
- Base URL: Configured in `config/models.py` 