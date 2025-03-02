import asyncio
import time
import pytest
from src.utils.rate_limiter import AsyncRateLimiter

@pytest.mark.asyncio
async def test_rate_limiter():
    # Set up a rate limiter allowing 5 operations per second.
    max_rate = 5
    time_period = 1  # second
    limiter = AsyncRateLimiter(max_rate, time_period)
    
    # Define an async function that simulates an operation protected by the rate limiter.
    async def limited_op():
        async with limiter:
            # Operation simulated by a negligible delay.
            return 1

    start_time = time.monotonic()
    # Launch 10 operations concurrently.
    results = await asyncio.gather(*(limited_op() for _ in range(10)))
    end_time = time.monotonic()
    elapsed = end_time - start_time

    # With max_rate of 5 per second, the first 5 operations proceed immediately,
    # but the next 5 must wait for tokens to refill.
    # We expect the total elapsed time to be at least 1 second.
    assert elapsed >= 1, f"Elapsed time {elapsed} is less than expected for rate limiting"
    # Check that all operations returned the expected value.
    assert all(result == 1 for result in results)