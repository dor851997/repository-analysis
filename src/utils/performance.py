import time
import functools
import logging

logger = logging.getLogger(__name__)

def measure_time(func):
    """Async decorator to measure execution time of a function."""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = await func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        logger.info(f"{func.__name__} took {elapsed:.4f} seconds")
        return result
    return wrapper