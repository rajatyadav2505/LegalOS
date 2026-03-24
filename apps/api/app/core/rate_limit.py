from __future__ import annotations

import asyncio
import time
from collections import deque
from dataclasses import dataclass
from functools import lru_cache


@dataclass(slots=True)
class RateLimitState:
    allowed: bool
    retry_after_seconds: int


class InMemoryRateLimiter:
    def __init__(self) -> None:
        self._attempts: dict[str, deque[float]] = {}
        self._lock = asyncio.Lock()

    async def evaluate(self, *, key: str, limit: int, window_seconds: int) -> RateLimitState:
        async with self._lock:
            attempts = self._prune(key=key, window_seconds=window_seconds)
            if len(attempts) >= limit:
                retry_after = max(1, int(window_seconds - (time.monotonic() - attempts[0])))
                return RateLimitState(allowed=False, retry_after_seconds=retry_after)
            return RateLimitState(allowed=True, retry_after_seconds=0)

    async def record_failure(self, *, key: str, window_seconds: int) -> None:
        async with self._lock:
            attempts = self._prune(key=key, window_seconds=window_seconds)
            attempts.append(time.monotonic())

    async def reset(self, *, key: str) -> None:
        async with self._lock:
            self._attempts.pop(key, None)

    def _prune(self, *, key: str, window_seconds: int) -> deque[float]:
        now = time.monotonic()
        attempts = self._attempts.setdefault(key, deque())
        while attempts and (now - attempts[0]) >= window_seconds:
            attempts.popleft()
        if not attempts:
            self._attempts.pop(key, None)
            attempts = self._attempts.setdefault(key, deque())
        return attempts


@lru_cache(maxsize=1)
def get_login_rate_limiter() -> InMemoryRateLimiter:
    return InMemoryRateLimiter()
