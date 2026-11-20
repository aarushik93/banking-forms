from __future__ import annotations

import threading
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request, status

from app.config import get_settings


class SlidingWindowRateLimiter:
    """Per-key sliding one-minute window.

    In-memory, so limits apply per instance; swap for a Redis-backed limiter
    when running more than one replica behind a load balancer.
    """

    def __init__(self, limit_per_minute: int) -> None:
        self.limit = limit_per_minute
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def allow(self, key: str) -> bool:
        if self.limit <= 0:  # disabled
            return True
        now = time.monotonic()
        cutoff = now - 60
        with self._lock:
            q = self._hits[key]
            while q and q[0] < cutoff:
                q.popleft()
            if len(q) >= self.limit:
                return False
            q.append(now)
            return True


_limiter: SlidingWindowRateLimiter | None = None


def _get_limiter() -> SlidingWindowRateLimiter:
    global _limiter
    if _limiter is None:
        _limiter = SlidingWindowRateLimiter(get_settings().rate_limit_per_minute)
    return _limiter


async def rate_limit(request: Request) -> None:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        key = forwarded.split(",")[0].strip()
    else:
        key = request.client.host if request.client else "unknown"
    if not _get_limiter().allow(key):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests, please slow down.",
        )
