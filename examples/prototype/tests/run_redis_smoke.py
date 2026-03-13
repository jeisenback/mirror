import asyncio
import os
import sys

# ensure imports work when run from repo root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from bus.redis_async_adapter import AsyncRedisStreamBus
from executor.worker import AsyncTaskExecutor
from models.mock_provider import MockModelProvider
from belief_store.store import BeliefStore
import skills.lead_qualification as lead_skill


async def main():
    redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    bus = AsyncRedisStreamBus(url=redis_url)
    belief_store = BeliefStore()
    crm = []
    model = MockModelProvider()
    skills_registry = {'lead_qualification': lead_skill.run}

    executor = AsyncTaskExecutor(bus, skills_registry, model, belief_store, crm)

    # publish two envelopes directly (adapter helpers are sync)
    import uuid
    envelopes = [
        {'id': str(uuid.uuid4()), 'type': 'lead_qualification', 'input': {'name': 'Small Co', 'email': 'a@small.co', 'revenue': 50000}},
        {'id': str(uuid.uuid4()), 'type': 'lead_qualification', 'input': {'name': 'Big Co', 'email': 'b@big.co', 'revenue': 200000}},
    ]

    for e in envelopes:
        await bus.publish(e)

    # process the two messages
    processed = 0
    for _ in range(10):
        ok = await executor.process_one(block_ms=1000)
        if ok:
            processed += 1
        else:
            # no message
            break

    # quick assertions
    assert processed >= 2, f"Expected to process at least 2 messages, got {processed}"
    print('Redis smoke test passed; processed', processed)


if __name__ == '__main__':
    asyncio.run(main())
