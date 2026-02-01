# Root Cause Analysis: LRU Cache Eviction Bug

## Bug Investigation

### Observed Failures

Running `pytest test_lru_cache.py -v` showed 4 failing tests:

1. **test_eviction_at_capacity**: After putting ("a",1), ("b",2), ("c",3), then put("d",4), the test expects get("a") is None (evicted) and get("d") == 4. Instead, get("a") returned 4 and get("d") returned None.

2. **test_single_capacity_cache**: With capacity 1, put("a",1) then put("b",2). Expected get("a") is None, get("b") == 2. Instead get("a") returned 2.

3. **test_get_updates_recency** and **test_put_updates_recency**: Similar pattern — the value meant for the new key was stored under the evicted key.

### Hypotheses

- The eviction logic was not actually removing the LRU item; it was overwriting the LRU key's value with the new value and moving that key to the end. So the *new key* was never inserted, and the evicted key stayed in the cache with the wrong value.

### Narrowing Down

Inspecting `put()` when at capacity:

```python
lru_key = next(iter(self._cache))
self._cache[lru_key] = value
self._cache.move_to_end(lru_key)
```

This assigns `value` to `lru_key` (the key we intend to evict) and moves that key to the end. So we never add the new `key`; we only reuse the LRU key's slot for the new value. That explains why get(new_key) is None and get(evicted_key) returns the new value.

---

## Root Cause Identification

### Root Cause

The eviction block **overwrites the LRU key's value** with the new value and moves that key to the end, instead of **deleting the LRU key** and **inserting the new key**.

So:

- The new key is never added to the cache.
- The “evicted” key remains in the cache with the new value.
- Eviction is not happening; only value reuse on the wrong key.

### Why This Causes the Failures

- **test_eviction_at_capacity**: put("d", 4) sets _cache["a"] = 4 and move_to_end("a"). So the cache has keys "a", "b", "c" with "a" → 4. get("a") == 4, get("d") is None.
- **test_single_capacity_cache**: put("b", 2) sets _cache["a"] = 2. So the only key is "a" with value 2. get("a") == 2, get("b") is None.

### Logical Flaw

When at capacity we must:

1. Remove the least recently used item (delete its key from the cache).
2. Add the new (key, value).

The code did (1) only in spirit by choosing `lru_key`, but then (2) updated `_cache[lru_key] = value` and move_to_end(lru_key), which is “update LRU key and make it MRU” instead of “remove LRU, then add new key.”

### Problematic Code (lru_cache.py)

Lines 65–71 (before fix):

```python
if len(self._cache) >= self.capacity:
    lru_key = next(iter(self._cache))
    self._cache[lru_key] = value
    self._cache.move_to_end(lru_key)
else:
    self._cache[key] = value
```

- `self._cache[lru_key] = value` reuses the LRU key for the new value instead of deleting it.
- The new `key` is never written to `_cache`, so the new key is never in the cache.

---

## Minimal Reproduction

```python
from lru_cache import LRUCache

cache = LRUCache(2)
cache.put("a", 1)
cache.put("b", 2)
# Cache full: order ["a", "b"]
cache.put("c", 3)  # Should evict "a", add "c"

assert cache.get("a") is None  # "a" should be evicted
assert cache.get("c") == 3     # "c" should be present
# Bug: get("a") returns 3, get("c") returns None
```

Exact sequence: fill to capacity, then put a new key. The evicted key keeps the new value; the new key is missing.

---

## Fix

**Correct behavior**: When at capacity, delete the LRU key, then add the new (key, value). No need for an else branch; after eviction we always add the new item.

**Corrected code** (in `lru_cache.py`):

```python
# If at capacity, evict least recently used
if len(self._cache) >= self.capacity:
    lru_key = next(iter(self._cache))
    del self._cache[lru_key]
self._cache[key] = value
```

- `del self._cache[lru_key]` actually removes the LRU item.
- `self._cache[key] = value` adds the new key; in OrderedDict this inserts at the end (MRU).

This addresses the root cause: eviction is now a real removal, and the new key is always inserted.
