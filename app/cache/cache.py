import json


class Cache:

    def __init__(
            self,
            redis
    ):
        self.redis = redis

    async def set(
        self,
        key: str,
        value,
        expire: int | None = None
    ):
        data = json.dumps(value)
        await self.redis.set(key, data, ex=expire)

    async def get(
            self,
            key: str
    ):
        data = await self.redis.get(key)

        if data is None:
            return None

        return json.loads(data)

    async def delete(
            self,
            key: str
    ):
        await self.redis.delete(key)
