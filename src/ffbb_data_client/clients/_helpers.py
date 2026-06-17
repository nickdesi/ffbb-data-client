from __future__ import annotations

import asyncio
import atexit
import threading
from collections.abc import Awaitable
from typing import TypeVar

T = TypeVar("T")


def present_items(items: list[T | None]) -> list[T]:
    return [item for item in items if item is not None]


class _BackgroundEventLoop:
    """Boucle d'événements persistante hébergée dans un thread dédié.

    Router tous les appels synchrones vers une boucle unique et durable permet
    de réutiliser le pool de connexions de l'``httpx.AsyncClient`` partagé
    (sockets TLS gardés chauds) au lieu de recréer/détruire une boucle — et donc
    de refaire un handshake TLS — à chaque appel sync.
    """

    def __init__(self) -> None:
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()

    def _ensure_started(self) -> asyncio.AbstractEventLoop:
        loop = self._loop
        if loop is not None and not loop.is_closed():
            return loop
        with self._lock:
            loop = self._loop
            if loop is not None and not loop.is_closed():
                return loop
            loop = asyncio.new_event_loop()
            thread = threading.Thread(
                target=self._run,
                args=(loop,),
                name="ffbb-async-loop",
                daemon=True,
            )
            thread.start()
            self._loop = loop
            self._thread = thread
            return loop

    @staticmethod
    def _run(loop: asyncio.AbstractEventLoop) -> None:
        asyncio.set_event_loop(loop)
        loop.run_forever()

    def run(self, coro: Awaitable[T]) -> T:
        loop = self._ensure_started()

        async def _await() -> T:
            return await coro

        future = asyncio.run_coroutine_threadsafe(_await(), loop)
        return future.result()

    def shutdown(self) -> None:
        loop = self._loop
        thread = self._thread
        if loop is None:
            return
        with self._lock:
            self._loop = None
            self._thread = None
        if not loop.is_closed():
            loop.call_soon_threadsafe(loop.stop)
        if thread is not None:
            thread.join(timeout=5)
        if not loop.is_closed():
            loop.close()


_background_loop = _BackgroundEventLoop()
atexit.register(_background_loop.shutdown)


def run_async(coro: Awaitable[T]) -> T:
    """Exécute une coroutine depuis un contexte synchrone.

    Toutes les coroutines sont dispatchées vers une boucle d'événements
    persistante dédiée (thread séparé), ce qui préserve la réutilisation des
    connexions HTTP entre appels. L'appel bloque le thread courant jusqu'au
    résultat, comme l'API synchrone le garantit.
    """
    return _background_loop.run(coro)
