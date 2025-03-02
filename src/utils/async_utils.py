# repository_analyzer/src/utils/async_utils.py

import asyncio
from typing import List, Any

async def run_concurrently(tasks: List[Any]) -> List[Any]:
    """
    Run a list of asynchronous tasks concurrently.
    """
    return await asyncio.gather(*tasks, return_exceptions=True)

async def safe_execute(coro):
    """
    Execute a coroutine safely by catching exceptions.
    """
    try:
        return await coro
    except Exception as e:
        print(f"Error: {e}")
        return None
