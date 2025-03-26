# AI Orchestrator Documentation

## Overview

The AI Orchestrator is a hierarchical system that coordinates multiple specialized AI services to process complex queries. By distributing cognitive tasks across specialized services, the system achieves more nuanced and comprehensive responses than a single LLM could provide.

## System Architecture

### Hierarchical Structure

The system follows a tree-like architecture with three tiers:

1. **Coordinator (Top Tier)**
   - **Atlas**: Central coordinator that delegates to specialized services and synthesizes final responses

2. **Mid-Level Specialists (Middle Tier)**
   - **Nova**: Technical branch that specializes in practical, implementation-focused analysis
   - **Sage**: Philosophical branch that focuses on concepts, theory, and principles

3. **Leaf Services (Bottom Tier)**
   - Under Nova:
     - **Echo**: Pattern recognition specialist
     - **Pixel**: Creative visualization specialist
   - Under Sage:
     - **Quantum**: Probabilistic reasoning specialist

### Processing Flow

Query processing follows this sequence:

1. User submits a query to Atlas
2. Atlas performs initial analysis and delegates to Nova and Sage
3. Nova and Sage analyze from their specialized perspectives and delegate to their respective sub-services
4. Leaf services (Echo, Pixel, Quantum) perform deep analysis in their domains
5. Results flow back up the hierarchy with each level synthesizing the inputs from below
6. Atlas receives synthesized results from Nova and Sage and creates a final response

## Core Components

### Base Service Framework

All services inherit from the `BaseService` class (in `core/services/base.py`), which provides:

- FastAPI server infrastructure
- Messaging system integration
- Lifecycle management (start/stop)
- LLM query capabilities
- Error handling

Services also inherit thinking capabilities from `BaseThinkingService` (in `core/services/base_thinking.py`), which provides:

- Standard thinking operations (analyze, reflect, critique, integrate)
- Delegation and response management
- Conversation context tracking
- System logging

### Messaging System

Services communicate through an asynchronous messaging system that:

- Uses routing keys for targeted messages
- Implements publish/subscribe patterns
- Maintains correlation IDs for tracking message threads
- Allows for structured contexts in messages

### Rate Limiting and Timing Strategy

To prevent LLM overload and create a natural cognitive flow, the system implements carefully managed timing:

- Each service follows sequential LLM calls with deliberate delays between steps
- Sub-services start with staggered delays (Echo → Pixel → Quantum)
- Parent services wait appropriate times before synthesizing results

Timing constants are centralized in `config/timing.py`:
- `DELAY_BETWEEN_LLM_CALLS`: 10 seconds between LLM calls within each service
- `DELAY_BEFORE_SYNTHESIS`: 10 seconds before synthesizing sub-service responses
- Service-specific startup delays (Echo: 0s, Pixel: 5s, Quantum: 10s)

### Database and Logging

The system maintains detailed logs of:

- Conversations and queries
- All internal messages
- Thinking operations
- Processing metrics

Data models are defined in `database/models.py` and include:
- `Conversation`: Query sessions
- `Message`: Internal and external communications
- `ProcessingMetrics`: Performance tracking

## Service Details

### Atlas Service

**Purpose**: Overall coordinator and synthesizer

**Key Methods**:
- `handle_user_query()`: Entry point for user queries
- `delegate_to_specialists()`: Distributes tasks to Nova and Sage
- `synthesize_final_response()`: Creates comprehensive response from specialist inputs

### Nova Service

**Purpose**: Technical analysis coordinator

**Key Methods**:
- `analyze()`: Technical perspective analysis
- `delegate_to_specialists()`: Distributes tasks to Echo and Pixel
- `synthesize_responses()`: Combines sub-service inputs

### Sage Service

**Purpose**: Philosophical analysis coordinator

**Key Methods**:
- `analyze()`: Conceptual perspective analysis
- `delegate_to_specialists()`: Distributes tasks to Quantum
- `synthesize_responses()`: Processes sub-service inputs

### Echo Service

**Purpose**: Pattern recognition specialist

**Key Methods**:
- `analyze()`: Pattern identification
- `reflect()`: Pattern significance exploration
- `critique()`: Pattern validity assessment
- `integrate()`: Pattern insights synthesis

### Pixel Service

**Purpose**: Creative visualization specialist

**Key Methods**:
- `analyze()`: Visual element analysis
- `reflect()`: Visual meaning exploration
- `critique()`: Visual approach assessment
- `integrate()`: Visual insights synthesis

### Quantum Service

**Purpose**: Probabilistic reasoning specialist

**Key Methods**:
- `analyze()`: Probability space analysis
- `reflect()`: Alternative scenario exploration
- `critique()`: Reasoning validity assessment
- `integrate()`: Probabilistic insights synthesis

## Thinking Process

Each service implements a 4-step thinking process:

1. **Analysis**: Initial domain-specific analysis
2. **Reflection**: Deeper consideration of own analysis
3. **Critique**: Critical examination of thinking
4. **Integration**: Combining insights into cohesive understanding

This process creates more nuanced and self-reflective thinking than a single-pass analysis.

## Context Enrichment

Services enrich message context as they process information:

- Parent services include their analysis in messages to child services
- Each service maintains thinking chains that track cognitive progression
- Branch paths record the journey of a message through the system
- Thinking depth tracks recursive thought operations

## System Operation

### Starting Services

Services can be started using the `start_services.bat` script, which launches each service in a separate terminal window.

Services should be started in this order:
1. Atlas
2. Nova and Sage
3. Echo, Pixel, and Quantum

Each service runs as a separate FastAPI application on a dedicated port.

### Configuration

System configuration is distributed across several files:
- `config/services.py`: Service definitions and capabilities
- `config/models.py`: LLM model configuration
- `config/timing.py`: Timing and delay settings
- `config/settings.py`: General system settings

### Prompt Templates

Each service has a dedicated prompts class (e.g., `EchoPrompts`) that provides specialized prompt templates for different thinking operations.

## Recent Improvements

1. **Timing Strategy**: Implemented deliberate delays to prevent LLM overload and create natural thinking flow
2. **Context Propagation**: Enhanced parent analysis sharing with child services
3. **Error Handling**: Standardized error response system across all services
4. **Code Optimization**: Removed vestigial code and consolidated common functionality
5. **Configuration Centralization**: Moved timing constants to central configuration 