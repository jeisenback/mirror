"""Runtime helpers for selecting a bus implementation.

Exports `get_bus()` which returns an instance of the preferred bus:
- If `REDIS_URL` env var is present and `redis.asyncio` is importable, returns
  `AsyncRedisStreamBus`.
- Otherwise returns `InMemoryBus` for local runs and tests.
"""
import os

try:
    from bus.redis_async_adapter import AsyncRedisStreamBus
    _HAS_ASYNC_REDIS = True
except Exception:
    try:
        from examples.prototype.bus.redis_async_adapter import AsyncRedisStreamBus
        _HAS_ASYNC_REDIS = True
    except Exception:
        try:
            from .bus.redis_async_adapter import AsyncRedisStreamBus
            _HAS_ASYNC_REDIS = True
        except Exception:
            AsyncRedisStreamBus = None
            _HAS_ASYNC_REDIS = False

try:
    from bus.in_memory import InMemoryBus
except Exception:
    try:
        from examples.prototype.bus.in_memory import InMemoryBus
    except Exception:
        from .bus.in_memory import InMemoryBus


def get_bus():
    redis_url = os.environ.get('REDIS_URL')
    if redis_url and _HAS_ASYNC_REDIS:
        return AsyncRedisStreamBus(url=redis_url)
    # fallback to in-memory bus for local/testing
    return InMemoryBus()
