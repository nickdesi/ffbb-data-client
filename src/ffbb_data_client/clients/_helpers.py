from __future__ import annotations

import asyncio
import concurrent.futures
from collections.abc import Awaitable
from typing import TypeVar

T = TypeVar("T")


def present_items(items: list[T | None]) -> list[T]:
    return [item for item in items if item is not None]


def run_async(coro: Awaitable[T]) -> T:
    """Run an async coroutine from sync context, handling nested event loops."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future: concurrent.futures.Future[T] = executor.submit(asyncio.run, coro)  # type: ignore[arg-type]
            return future.result()
    elif loop:
        return loop.run_until_complete(coro)
    else:
        return asyncio.run(coro)  # type: ignore[arg-type]
