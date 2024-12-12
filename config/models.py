import os
from typing import Dict, Any, Optional
from pydantic import BaseModel, ConfigDict

class ModelParameters(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    
    name: str = "phi-3"  # Simplified name, we'll construct the full path in query
    slot: Optional[int] = None
    temperature: float = 0.7
    max_tokens: int = 4096
    top_p: float = 0.9

class ModelConfig(BaseModel):
    base_url: str
    models: Dict[str, ModelParameters]

    @classmethod
    def from_env(cls) -> 'ModelConfig':
        base_config = {
            'temperature': 0.7,
            'max_tokens': 4096,
            'top_p': 0.9
        }
        
        services = ['atlas', 'nova', 'sage', 'echo', 'pixel', 'quantum']
        models = {}
        
        for service in services:
            models[service] = ModelParameters(
                name="phi-3",
                slot=None if service == 'atlas' else {
                    'nova': 2, 'sage': 3, 'echo': 4,
                    'pixel': 5, 'quantum': 6
                }[service],
                temperature=float(os.getenv(f'{service.upper()}_TEMP', base_config['temperature'])),
                max_tokens=int(os.getenv(f'{service.upper()}_MAX_TOKENS', base_config['max_tokens'])),
                top_p=float(os.getenv(f'{service.upper()}_TOP_P', base_config['top_p']))
            )
        
        return cls(
            base_url=os.getenv('LMSTUDIO_BASE_URL', 'http://localhost:1234/v1'),
            models=models
        )

# Create global model configuration
MODEL_CONFIG = ModelConfig.from_env()

# Add debug print
print("MODEL_CONFIG initialized with:")
for service, params in MODEL_CONFIG.models.items():
    print(f"{service}: slot={params.slot}, temp={params.temperature}")