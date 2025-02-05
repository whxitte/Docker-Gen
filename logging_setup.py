# logging_setup.py
import logging
from logging.handlers import RotatingFileHandler

def setup_logging(verbose: bool = False) -> None:
    """Configure logging with rotation and verbosity."""
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            RotatingFileHandler('docker-gen.log', maxBytes=10 * 1024 * 1024, backupCount=5),
            logging.StreamHandler()
        ]
    )
    logging.getLogger('openai').setLevel(logging.WARNING)
