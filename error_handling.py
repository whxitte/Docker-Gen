# error_handling.py
import logging
from functools import wraps

def handle_errors(func):
    """Decorator to catch exceptions and log detailed error messages."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logging.error(f"Error in {func.__name__}: {str(e)}")
            raise
    return wrapper
