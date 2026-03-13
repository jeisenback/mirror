import redis


class RedisStreamBus:
    """A minimal Redis Streams adapter for prototype use.

    Notes:
    - Uses redis-py sync client. For production, consider async or robust reconnect logic.
    - Exposes `publish`, `consume_one`, and `empty` similar to the in-memory bus.
    """

    def __init__(self, url='redis://localhost:6379/0', stream='mve_tasks', group='mve_group', consumer='consumer-1'):
        self.client = redis.Redis.from_url(url)
        self.stream = stream
        self.group = group
        self.consumer = consumer
        # create group if not exists
        try:
            self.client.xgroup_create(self.stream, self.group, id='0', mkstream=True)
        except redis.exceptions.ResponseError:
            # group already exists
            pass

    def publish(self, envelope: dict):
        # Redis requires mapping of string->string/bytes
        flat = {k: str(v) for k, v in envelope.items()}
        return self.client.xadd(self.stream, flat)

    def consume_one(self, block_ms: int = 1000):
        # Reads one entry for this consumer (blocking)
        res = self.client.xreadgroup(self.group, self.consumer, {self.stream: '>'}, count=1, block=block_ms)
        if not res:
            return None
        _, entries = res[0]
        eid, fields = entries[0]
        # convert bytes to str
        env = {k.decode('utf-8'): v.decode('utf-8') for k, v in fields.items()}
        env['id'] = eid.decode('utf-8')
        # ack the message
        try:
            self.client.xack(self.stream, self.group, eid)
        except Exception:
            pass
        return env

    def empty(self):
        info = self.client.xinfo_stream(self.stream)
        # approximate: length == 0
        return info.get('length', 0) == 0
