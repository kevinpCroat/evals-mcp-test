"""
LRU (Least Recently Used) Cache Implementation

A cache that evicts the least recently used items when it reaches capacity.
Items are considered "used" when they are accessed (get) or added (put).
"""

from typing import Any, Optional
from collections import OrderedDict


class LRUCache:
    """
    A Least Recently Used (LRU) cache with a fixed capacity.

    When the cache reaches its capacity, the least recently used item
    is evicted to make room for new items.
    """

    def __init__(self, capacity: int):
        """
        Initialize the LRU cache with a given capacity.

        Args:
            capacity: Maximum number of items the cache can hold
        """
        if capacity <= 0:
            raise ValueError("Capacity must be positive")

        self.capacity = capacity
        self._cache = OrderedDict()

    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from the cache.

        Args:
            key: The key to retrieve

        Returns:
            The value associated with the key, or None if not found
        """
        if key not in self._cache:
            return None

        # Mark as recently used by moving to end
        value = self._cache[key]
        self._cache.move_to_end(key)
        return value

    def put(self, key: str, value: Any) -> None:
        """
        Add or update a key-value pair in the cache.

        Args:
            key: The key to store
            value: The value to associate with the key
        """
        # If key exists, update it
        if key in self._cache:
            self._cache[key] = value
            self._cache.move_to_end(key)
            return

        # If at capacity, evict least recently used
        if len(self._cache) >= self.capacity:
            lru_key = next(iter(self._cache))
            del self._cache[lru_key]
        self._cache[key] = value

    def size(self) -> int:
        """
        Get the current number of items in the cache.

        Returns:
            The number of items currently in the cache
        """
        return len(self._cache)

    def clear(self) -> None:
        """
        Remove all items from the cache.
        """
        self._cache.clear()

    def __contains__(self, key: str) -> bool:
        """
        Check if a key exists in the cache.

        Args:
            key: The key to check

        Returns:
            True if the key exists, False otherwise
        """
        return key in self._cache

    def keys(self):
        """
        Get all keys in the cache (in LRU order, oldest first).

        Returns:
            A view of the cache keys
        """
        return self._cache.keys()
