import asyncio
import time

class AsyncRateLimiter:
    """
    A simple asynchronous rate limiter that allows a maximum number of
    operations per time period.
    """
    def __init__(self, max_rate: int, time_period: float):
        self._max_rate = max_rate
        self._time_period = time_period
        self._tokens = max_rate
        self._last_check = time.monotonic()
        self._lock = asyncio.Lock()

    async def __aenter__(self):
        async with self._lock:
            current = time.monotonic()
            elapsed = current - self._last_check
            # Refill tokens based on elapsed time.
            refill_tokens = int(elapsed * (self._max_rate / self._time_period))
            if refill_tokens > 0:
                self._tokens = min(self._tokens + refill_tokens, self._max_rate)
                self._last_check = current
            # If no tokens available, wait until at least one token is available.
            while self._tokens <= 0:
                await asyncio.sleep(self._time_period / self._max_rate)
                current = time.monotonic()
                elapsed = current - self._last_check
                refill_tokens = int(elapsed * (self._max_rate / self._time_period))
                if refill_tokens > 0:
                    self._tokens = min(self._tokens + refill_tokens, self._max_rate)
                    self._last_check = current
            # Consume a token.
            self._tokens -= 1
        return self

    async def __aexit__(self, exc_type, exc, tb):
        # Nothing special to do on exit.
        pass