from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Any


@dataclass
class CacheItem:
    value: Any
    expires_at: float


class SessionCache:
    def __init__(self) -> None:
        self._store: dict[str, CacheItem] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Any | None:
        async with self._lock:
            item = self._store.get(key)
            if not item:
                return None
            if item.expires_at < time.time():
                self._store.pop(key, None)
                return None
            return item.value

    async def set(self, key: str, value: Any, ttl_seconds: int = 600) -> None:
        async with self._lock:
            self._store[key] = CacheItem(value=value, expires_at=time.time() + ttl_seconds)

    async def clear(self) -> None:
        async with self._lock:
            self._store.clear()


session_cache = SessionCache()
