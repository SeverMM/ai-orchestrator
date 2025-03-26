"""
Configuration for system-wide timing and delays
"""

# Delays between LLM calls to prevent rate limiting/overload
DELAY_BETWEEN_LLM_CALLS = 10  # seconds

# Service synthesis delays
DELAY_BEFORE_SYNTHESIS = 10  # seconds

# Staggered startup delays for leaf services
DELAY_ECHO_STARTUP = 0  # seconds (starts immediately)
DELAY_PIXEL_STARTUP = 5  # seconds (starts after Echo)
DELAY_QUANTUM_STARTUP = 10  # seconds (starts after Pixel) 