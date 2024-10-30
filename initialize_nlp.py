import logging
import re
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_text_processing():
    """Initialize basic text processing setup"""
    try:
        # Create necessary directories
        Path('uploads').mkdir(exist_ok=True)
        
        # Test regex patterns
        test_patterns = {
            'skills': r'\b(python|java|javascript)\b',
            'location': r'(?:Location|Based in):\s*([\w\s,]+)'
        }
        
        # Verify pattern compilation
        for name, pattern in test_patterns.items():
            try:
                re.compile(pattern)
                logger.info(f"Successfully compiled {name} pattern")
            except re.error as e:
                logger.error(f"Error compiling {name} pattern: {str(e)}")
                return False
        
        logger.info("Text processing setup completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error in text processing setup: {str(e)}")
        return False

if __name__ == "__main__":
    setup_text_processing()
