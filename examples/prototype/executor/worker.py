import uuid
import asyncio
import inspect
from typing import Any


def _is_coro_fn(fn):
    return inspect.iscoroutinefunction(fn)


async def _awaitable_call(fn, *args, **kwargs):
    if _is_coro_fn(fn):
        return await fn(*args, **kwargs)
    # bound methods may be regular functions; run in thread
    return await asyncio.to_thread(fn, *args, **kwargs)


class AsyncTaskExecutor:
    def __init__(self, bus, skills_registry, model_provider, belief_store, crm):
        self.bus = bus
        self.skills = skills_registry
        self.model_provider = model_provider
        self.belief_store = belief_store
        self.crm = crm

    async def _execute_skill(self, task: dict) -> Any:
        ttype = task.get('type')
        if ttype in self.skills:
            skill = self.skills[ttype]
            # support async or sync skills
            if _is_coro_fn(skill):
                return await skill(task, self.model_provider, self.belief_store, self.crm)
            else:
                return await asyncio.to_thread(skill, task, self.model_provider, self.belief_store, self.crm)
        else:
            raise RuntimeError(f"Unknown task type: {ttype}")

    async def process_one(self, block_ms: int = 1000) -> bool:
        try:
            env = await _awaitable_call(self.bus.consume_one, block_ms)
        except TypeError:
            env = await _awaitable_call(self.bus.consume_one)
        if not env:
            return False
        try:
            await self._execute_skill(env)
        except Exception as e:
            await _awaitable_call(self.belief_store.record_step, {
                'step_id': str(uuid.uuid4()),
                'task_id': env.get('id'),
                'error': str(e)
            })
        return True

    async def process_all(self):
        while not await _awaitable_call(self.bus.empty):
            await self.process_one()


class TaskExecutor:
    """Sync wrapper around the async executor for local runs and tests.

    Note: uses `asyncio.run` and therefore should not be called from an existing
    event loop (e.g., inside an async webserver). For server contexts use
    `AsyncTaskExecutor` directly.
    """

    def __init__(self, bus, skills_registry, model_provider, belief_store, crm):
        self._async = AsyncTaskExecutor(bus, skills_registry, model_provider, belief_store, crm)

    def process_one(self, block_ms: int = 1000) -> bool:
        return asyncio.run(self._async.process_one(block_ms=block_ms))

    def process_all(self):
        return asyncio.run(self._async.process_all())
