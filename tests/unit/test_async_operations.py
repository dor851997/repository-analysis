import asyncio
import time
import pytest
from src.core.assistant import measure_time

# -------------------------------------------------------------------
# Dummy asynchronous functions for testing
# -------------------------------------------------------------------

async def dummy_work(delay: float) -> str:
    """Simulates asynchronous work by sleeping for 'delay' seconds."""
    await asyncio.sleep(delay)
    return "done"

@measure_time
async def wrapped_dummy_work(delay: float) -> str:
    """A dummy work function wrapped with the performance decorator."""
    return await dummy_work(delay)

async def dummy_error_work(delay: float) -> str:
    """Simulates asynchronous work that fails after a delay."""
    await asyncio.sleep(delay)
    raise ValueError("Intentional error for testing.")

@measure_time
async def wrapped_error_work(delay: float) -> str:
    """Wraps the error-inducing function with the performance decorator."""
    return await dummy_error_work(delay)

# -------------------------------------------------------------------
# Test asynchronous operations
# -------------------------------------------------------------------

@pytest.mark.asyncio
async def test_dummy_work_concurrency():
    """
    Test that multiple asynchronous tasks run concurrently.
    Two tasks that each sleep for 0.5 seconds should complete in less than 0.8 seconds total.
    """
    start_time = time.perf_counter()
    results = await asyncio.gather(dummy_work(0.5), dummy_work(0.5))
    elapsed = time.perf_counter() - start_time

    # Since tasks run concurrently, the total elapsed time should be near 0.5 seconds.
    assert elapsed < 0.8, f"Concurrency failed, elapsed time: {elapsed}"
    assert results == ["done", "done"]

@pytest.mark.asyncio
async def test_measure_time_decorator():
    """
    Test the measure_time decorator by ensuring the wrapped function returns the expected result
    and its execution time is in the expected range.
    """
    start_time = time.perf_counter()
    result = await wrapped_dummy_work(0.5)
    elapsed = time.perf_counter() - start_time

    # Verify the function returns the expected output.
    assert result == "done"
    # Allow a small overhead; the total elapsed time should be roughly 0.5 seconds.
    assert 0.5 <= elapsed < 0.8, f"Elapsed time {elapsed} is not within expected range."

@pytest.mark.asyncio
async def test_error_in_wrapped_function():
    """
    Test that errors in an async function wrapped with the measure_time decorator are propagated.
    """
    with pytest.raises(ValueError, match="Intentional error for testing."):
        await wrapped_error_work(0.1)