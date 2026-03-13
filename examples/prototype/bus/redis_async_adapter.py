import asyncio
import time
from typing import Optional

import redis.asyncio as aioredis


class AsyncRedisStreamBus:
    """Async Redis Streams adapter using redis.asyncio with simple retries.

    This coexists with the sync adapter. It provides `publish`, `consume_one`,
    and `empty` as async methods.
    """

    def __init__(self, url: str = 'redis://localhost:6379/0', stream: str = 'mve_tasks',
                 group: str = 'mve_group', consumer: str = 'consumer-1', max_retries: int = 3):
        self.url = url
        self.stream = stream
        self.group = group
        self.consumer = consumer
        self.max_retries = max_retries
        self.client: Optional[aioredis.Redis] = None

    async def _ensure_client(self):
        if self.client is None:
            self.client = aioredis.from_url(self.url)
            # try to create group; ignore if exists
            try:
                await self.client.xgroup_create(self.stream, self.group, id='0', mkstream=True)
            except Exception:
                pass

    async def _with_retries(self, coro, *args, **kwargs):
        delay = 0.1
        for attempt in range(1, self.max_retries + 1):
            try:
                return await coro(*args, **kwargs)
            except Exception as e:
                if attempt == self.max_retries:
                    raise
                await asyncio.sleep(delay)
                delay = min(2.0, delay * 2)

    async def publish(self, envelope: dict):
        await self._ensure_client()
        flat = {k: str(v) for k, v in envelope.items()}
        return await self._with_retries(self.client.xadd, self.stream, flat)

    async def consume_one(self, block_ms: int = 1000):
        await self._ensure_client()
        res = await self._with_retries(self.client.xreadgroup, self.group, self.consumer,
                                       {self.stream: '>'}, count=1, block=block_ms)
        if not res:
            return None
        _, entries = res[0]
        eid, fields = entries[0]
        env = {k.decode('utf-8') if isinstance(k, bytes) else k: (v.decode('utf-8') if isinstance(v, bytes) else v)
               for k, v in fields.items()}
        env['id'] = eid.decode('utf-8') if isinstance(eid, bytes) else str(eid)
        try:
            await self.client.xack(self.stream, self.group, eid)
        except Exception:
            pass
        return env

    async def empty(self):
        await self._ensure_client()
        info = await self.client.xinfo_stream(self.stream)
        return info.get('length', 0) == 0
