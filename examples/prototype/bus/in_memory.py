import collections

class InMemoryBus:
    def __init__(self):
        self._queue = collections.deque()

    def publish(self, envelope):
        self._queue.append(envelope)

    def consume_one(self):
        if self._queue:
            return self._queue.popleft()
        return None

    def empty(self):
        return len(self._queue) == 0
