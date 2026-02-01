"""
Thread-safe cache implementation using threading.Lock.

Uses a lock to make get/put/stats and hits/misses/eviction atomic.
"""

import threading
from typing import Any, Optional


class SimpleCache:
    """A simple in-memory cache, thread-safe via Lock."""

    def __init__(self, max_size: int = 100):
        self.cache = {}
        self.max_size = max_size
        self.hits = 0
        self.misses = 0
        self._lock = threading.Lock()

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache. Returns None if not found."""
        with self._lock:
            if key in self.cache:
                self.hits += 1
                return self.cache[key]
            else:
                self.misses += 1
                return None

    def put(self, key: str, value: Any) -> None:
        """Put value in cache."""
        with self._lock:
            if len(self.cache) >= self.max_size and self.cache:
                first_key = next(iter(self.cache))
                del self.cache[first_key]
            self.cache[key] = value

    def get_stats(self) -> dict:
        """Get cache statistics."""
        with self._lock:
            total = self.hits + self.misses
            hit_rate = self.hits / total if total > 0 else 0.0
            return {
                'hits': self.hits,
                'misses': self.misses,
                'hit_rate': hit_rate,
                'size': len(self.cache)
            }

    def clear(self) -> None:
        """Clear the cache."""
        with self._lock:
            self.cache = {}
            self.hits = 0
            self.misses = 0
