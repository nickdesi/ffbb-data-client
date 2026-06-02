"""Outils de concurrence asynchrone pour FFBB Data Client."""

from __future__ import annotations

import asyncio
from collections.abc import Coroutine
from typing import Any, TypeVar

T = TypeVar("T")


async def gather_with_concurrency(
    max_concurrency: int,
    *tasks: Coroutine[Any, Any, T],
) -> list[T]:
    """
    Exécute plusieurs tâches asynchrones en parallèle tout en limitant le nombre
    de tâches simultanées à l'aide d'un sémaphore.

    Args:
        max_concurrency: Le nombre maximum de tâches à exécuter en même temps.
        *tasks: Les coroutines des tâches à exécuter.

    Returns:
        La liste des résultats des tâches dans l'ordre d'origine.
    """
    semaphore = asyncio.Semaphore(max_concurrency)

    async def sem_task(task: Coroutine[Any, Any, T]) -> T:
        async with semaphore:
            return await task

    return await asyncio.gather(*(sem_task(task) for task in tasks))
