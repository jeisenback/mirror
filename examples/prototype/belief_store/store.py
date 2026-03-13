import json

class BeliefStore:
    def __init__(self, path=None):
        self.path = path
        self._buffer = []

    def record_step(self, data):
        self._buffer.append(data)
        if self.path:
            with open(self.path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(data) + '\n')

    def all(self):
        return list(self._buffer)
