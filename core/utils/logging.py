import logging
import sys
from typing import Optional

def setup_logger(name: str, level: Optional[int] = None) -> logging.Logger:
    """Configure and return a logger instance"""
    logger = logging.getLogger(name)
    
    if level is None:
        level = logging.INFO
    
    logger.setLevel(level)
    
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        
        logger.addHandler(handler)
    
    return logger