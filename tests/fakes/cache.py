class FakeCache:
    def __init__(self):
        self.data = {}

    async def set(self, key, value, expire=None):
        self.data[key] = value

    async def get(self, key):
        return self.data.get(key)

    async def delete(self, key):
        return self.data.pop(key, None) is not None

    redis = None